"""
运行Unity3D（MLAgents）策略服务器的示例，该服务器可以通过在许多已连接的Unity游戏客户端（可能在n个节点上的云端中运行）中进行采样来学习策略。
有关在本地运行的Unity3D示例，请参见：
`examples / unity3d_env_local.py` https://github.com/ray-project/ray/blob/master/rllib/examples/unity3d_env_local.py

要针对中央策略服务器在可能不同的计算机上运行此脚本（即可启用ray的分布式操作），请执行以下操作：
1) 安装Unity2019.4.20f1（推荐）或更高，然后使用Anaconda3创建虚拟环境(py 3.8)，配置ray、ray[rllib]和unity mlagents环境
    1.创建虚拟环境
    2.安装tensorflow/pytorch
    3.安装unity mlagents (默认安装最新版本)
        pip install mlagents
    4.安装ray (注意！！！！ 安装master版本或者日更的Nightlies版本)
        轮子链接 https://s3-us-west-2.amazonaws.com/ray-wheels/latest/ray-2.0.0.dev0-cp38-cp38-win_amd64.whl
        切到轮子下载地址 pip install ray-2.0.0.dev0-cp38-cp38-win_amd64.whl
    5.安装ray[rllib]
        pip install ray[rllib]
    6.安装ray[cluster]
        pip install ray[cluster]

2) 编译支持MLAgents的Unity3D示例游戏，例如3DBall或您自己创建的任何其他游戏 （其实就是把环境build成exe）
   将编译后的二进制文件放在unity3D_client客户端脚本可以访问的位置。

2.1)想找到一个现成的Unity3D MLAgent案例，你可以去 https://github.com/Unity-Technologies/ml-agents 下载（推荐下载main版本）
    下载完成后案例就在`.../ml-agents/Project/Assets/ML-Agents/Examples/`文件夹中
    直接使用Unity2019.4.20f1打开‘.../ml-agents/Project’文件夹即可

3)更改您的unity3D_server服务器代码，以使其获取unity客户端对应环境的观测状态和动作空间，
  不同的策略（在Unity3D MLAgent中称为“behaviors”）以及特定游戏的agent到策略的映射。
  或者，使用现有的两个环境（3DBall或SoccerStrikersVsGoalie）。
    其实支持更多，例如3DBallHard、GridFoodCollector、Pyramids等，具体去Unity3DEnv.py查看

4) 然后安装顺序运行以下脚本
$ python unity3d_server.py --env 3DBall
$ python unity3d_client.py --inference-mode=local --game [path to game binary]
"""

import argparse
import os

import ray
from ray.tune import register_env
from ray.rllib.agents.ppo import PPOTrainer
from ray.rllib.agents.ddpg import DDPGTrainer
from ray.rllib.agents.dqn import DQNTrainer
from ray.rllib.agents.a3c import A2CTrainer
from ray.rllib.env.policy_server_input import PolicyServerInput
from unity3d_env import Unity3DEnv
from ray.rllib.examples.env.random_env import RandomMultiAgentEnv

SERVER_ADDRESS = "localhost"
SERVER_PORT = 9900
CHECKPOINT_FILE = "last_checkpoint_{}.out"

parser = argparse.ArgumentParser()
parser.add_argument(
    "--env",
    type=str,
    default="SoccerTwos",
    choices=["3DBall","SoccerTwos","SoccerStrikersVsGoalie"],
    help="The name of the Env to run in the Unity3D editor. Either `3DBall` "
    "or `SoccerStrikersVsGoalie` (feel free to add more to this script!)")
parser.add_argument(
    "--port",
    type=int,
    default=SERVER_PORT,
    help="The Policy server's port to listen on for ExternalEnv client "
    "conections.")
parser.add_argument(
    "--checkpoint-freq",
    type=int,
    default=10,
    help="The frequency with which to create checkpoint files of the learnt "
    "Policies.")
parser.add_argument(
    "--no-restore",
    action="store_false",
    help="Whether to load the Policy "
    "weights from a previous checkpoint")

if __name__ == "__main__":
    args = parser.parse_args()
    ray.init()

    # Create a fake-env for the server. This env will never be used (neither
    # for sampling, nor for evaluation) and its obs/action Spaces do not
    # matter either (multi-agent config below defines Spaces per Policy).
    register_env("a2c_04", lambda c: RandomMultiAgentEnv(c))

    policies, policy_mapping_fn = \
        Unity3DEnv.get_policy_configs_for_game(args.env)

    # The entire config will be sent to connecting clients so they can
    # build their own samplers (and also Policy objects iff
    # `inference_mode=local` on clients' command line).
    config = {
        # Use the connector server to generate experiences.
        "input": (
            lambda ioctx: PolicyServerInput(ioctx, SERVER_ADDRESS, args.port)),
        # Use a single worker process (w/ SyncSampler) to run the server.
        "num_workers": 0,
        # Disable OPE, since the rollouts are coming from online clients.
        "input_evaluation": [],

        # Other settings.
        "lr": 0.0001,
        "lambda": 0.95,
        "gamma": 0.99,
        "vf_loss_coeff": 0.5,
        "entropy_coeff": 0.01,
        "train_batch_size": 4000,

        # "num_sgd_iter": 20,
        "rollout_fragment_length": 20,
        # "clip_param": 0.2,

        "model": {
            "fcnet_hiddens": [512, 512],
        },
        
        # Multi-agent setup for the particular env.
        "multiagent": {
            "policies": policies,
            "policy_mapping_fn": policy_mapping_fn,
        },
        "framework": "tf",
    }
    # config = {
    #     # Use the connector server to generate experiences.
    #     "input": (
    #         lambda ioctx: PolicyServerInput(ioctx, SERVER_ADDRESS, args.port)),
    #     # Use a single worker process (w/ SyncSampler) to run the server.
    #     "num_workers": 0,
    #     # Disable OPE, since the rollouts are coming from online clients.
    #     "input_evaluation": [],

    #     # Other settings.
    #     # === Model ===
    #     "actor_hiddens": [512, 512],
    #     "critic_hiddens": [512, 512],
    #     "n_step": 1,
    #     "model": {},
    #     "gamma": 0.99,

    #      # === Optimization ===
    #     "actor_lr": 0.001,
    #     "critic_lr": 0.001,
    #     "use_huber": False,#改动了
    #     "huber_threshold": 1.0,
    #     "l2_reg": 0.000001,
    #     "learning_starts": 1500,
    #     "rollout_fragment_length": 20,
    #     "train_batch_size": 4000,

        
    #     # "lambda": 0.95,
    #     # "sgd_minibatch_size": 256,
    #     # "num_sgd_iter": 20,
        
    #     # === Exploration ===
    #     "exploration_config":{
    #         # "type": "OrnsteinUhlenbeckNoise",
    #         "scale_timesteps": 10000,
    #         "initial_scale": 1.0,
    #         "final_scale": 0.02,
    #         "ou_base_scale": 0.1,
    #         "ou_theta": 0.15,
    #         "ou_sigma": 0.2,
    #     },
    #     "timesteps_per_iteration": 1000,
    #     "target_network_update_freq": 0, # Update the target network every `target_network_update_freq` steps.
    #     "tau": 0.002, # Update the target by \tau * policy + (1-\tau) * target_policy
    #     # === Replay buffer ===
    #     "buffer_size": 50000,
    #     "prioritized_replay": True,
    #     "prioritized_replay_alpha": 0.6,
    #     "prioritized_replay_beta": 0.4,
    #     "prioritized_replay_eps": 0.000001,
    #     "clip_rewards": False,
    #     # "clip_param": 0.2,
    #     "worker_side_prioritization": False,

        
    #     # Multi-agent setup for the particular env.
    #     "multiagent": {
    #         "policies": policies,
    #         "policy_mapping_fn": policy_mapping_fn,
    #     },
    #     "framework": "tf",
    # }
    # config = {
    #     # Use the connector server to generate experiences.
    #     "input": (
    #         lambda ioctx: PolicyServerInput(ioctx, SERVER_ADDRESS, args.port)),
    #     # Use a single worker process (w/ SyncSampler) to run the server.
    #     # one Unity running)!
    #     "num_workers": 0,#改动了
    #     # Works for both torch and tf.
    #     "framework": "tf",
    #     # Use GPUs iff `RLLIB_NUM_GPUS` env var set to > 0.
    #     "num_gpus": int(os.environ.get("RLLIB_NUM_GPUS", "0")),#改动了
    #     "worker_side_prioritization": False,
    #     "lr": 0.0001,
    #     "n_step": 1,
        
    #     "learning_starts": 500,
    #     "train_batch_size": 512,
    #     "rollout_fragment_length": 20,
    #     "target_network_update_freq": 2500,
    #     "timesteps_per_iteration": 100,
    #     "min_iter_time_s": 0,

    #      "multiagent": {
    #         "policies": policies,
    #         "policy_mapping_fn": policy_mapping_fn,
    #     },
    # }

    # Create the Trainer used for Policy serving.
    trainer = A2CTrainer(env="a2c_04", config=config)
    # trainer = DDPGTrainer(env="test", config=config)
    # trainer = DQNTrainer(env="3v3_unity_dqn01", config=config)

    # Attempt to restore from checkpoint if possible.
    checkpoint_path = CHECKPOINT_FILE.format(args.env)
    if not args.no_restore and os.path.exists(checkpoint_path):
        checkpoint_path = open(checkpoint_path).read()
        print("Restoring from checkpoint path", checkpoint_path)
        trainer.restore(checkpoint_path)

    # policy=trainer.get_policy('SoccerTwos')
    # model = policy.export_model('my_striker',onnx=9)
    # policy=trainer.get_policy('Goalie')
    # model = policy.export_model('my_goalie',onnx=9)
    # print('save model!!!!!!!!!!!!')
    
    # trainer.export_policy_model('my_striker','SoccerTwos',onnx=9)
    # trainer.export_policy_model('my_goalie','Goalie',onnx=9)
    # print('save model again!!!!!!!!!!!!')

    # Serving and training loop.
    count = 0
    while True:
        # Calls to train() will block on the configured `input` in the Trainer
        # config above (PolicyServerInput).
        print(trainer.train())
        if count % args.checkpoint_freq == 0:
            print("Saving learning progress to checkpoint file.")
            checkpoint = trainer.save()
            # Write the latest checkpoint location to CHECKPOINT_FILE,
            # so we can pick up from the latest one after a server re-start.
            with open(checkpoint_path, "w") as f:
                f.write(checkpoint)
        count += 1
