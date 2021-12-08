using System;
using System.Collections;
using System.Collections.Generic;
using Unity.MLAgents;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;
using Random = UnityEngine.Random;

public class SoccerEnvController : MonoBehaviour
{
    [System.Serializable]
    public class PlayerInfo
    {
        public AgentSoccer Agent;
        [HideInInspector]
        public Vector3 StartingPos;
        [HideInInspector]
        public Quaternion StartingRot;
        [HideInInspector]
        public Rigidbody Rb;
    }

    public Text ScoreText;
    //public Text PurpleText;
    public int bluescore = 0;
    public int purplescore = 0;

    public Text TouchText;
    private int blueTouch = 0;
    private int purpleTouch = 0;

    public Text DistanceText;
    private double blueDis = 0;
    private double purpleDis = 0;


    /// <summary>
    /// Max Academy steps before this platform resets
    /// </summary>
    /// <returns></returns>
    [Tooltip("Max Environment Steps")] public int MaxEnvironmentSteps = 25000;

    /// <summary>
    /// The area bounds.
    /// </summary>

    /// <summary>
    /// We will be changing the ground material based on success/failue
    /// </summary>

    public GameObject ball;
    [HideInInspector]
    public Rigidbody ballRb;
    Vector3 m_BallStartingPos;

    //List of Agents On Platform
    public List<PlayerInfo> AgentsList = new List<PlayerInfo>();

    private SoccerSettings m_SoccerSettings;


    private SimpleMultiAgentGroup m_BlueAgentGroup;
    private SimpleMultiAgentGroup m_PurpleAgentGroup;

    private int m_ResetTimer;

    private int winScore = 10;
    private GameObject resultPanel;
    private Text resultText;
    private Vector3 panelScale;

    void Start()
    {

        m_SoccerSettings = FindObjectOfType<SoccerSettings>();
        // Initialize TeamManager
        m_BlueAgentGroup = new SimpleMultiAgentGroup();
        m_PurpleAgentGroup = new SimpleMultiAgentGroup();
        ballRb = ball.GetComponent<Rigidbody>();
        m_BallStartingPos = new Vector3(ball.transform.position.x, ball.transform.position.y, ball.transform.position.z);
        foreach (var item in AgentsList)
        {
            item.StartingPos = item.Agent.transform.position;
            item.StartingRot = item.Agent.transform.rotation;
            item.Rb = item.Agent.GetComponent<Rigidbody>();
            if (item.Agent.team == Team.Blue)
            {
                m_BlueAgentGroup.RegisterAgent(item.Agent);
            }
            else
            {
                m_PurpleAgentGroup.RegisterAgent(item.Agent);
            }
        }
        ResetScene();
        resultPanel = GameObject.FindWithTag("ResultPanel");
        resultText = resultPanel.transform.GetChild(0).GetComponent<Text>();
        panelScale = resultPanel.transform.localScale;
        resultPanel.transform.localScale = new Vector3(0, 0, 0);
    }

    void FixedUpdate()
    {
        if (gameObject.CompareTag("ScoreField"))
        {
            ScoreText.text = "Score - " + bluescore + " : " + purplescore;
            TouchText.text = "Ball Touch - " + blueTouch + " : " + purpleTouch;
            DistanceText.text = "Running Distance - " + blueDis + " : " + purpleDis;
            // ScoreText.text = "Score - Blue " + bluescore + " : " + purplescore + " Purple";
            // TouchText.text = "Touch - Blue  " + blueTouch + " : " + purpleTouch + " Purple";
            // DistanceText.text = "Distance - Blue  " + blueDis + " : " + purpleDis + " Purple";
            // PurpleText.text = purplescore + "  Purple";
            if (bluescore >= winScore)
            {
                //Debug.Log("Blue Wins");
                resultPanel.transform.localScale = new Vector3(1, 1, 1);
                resultText.text = "You Win!";
                resultText.color = Color.green;
                StartCoroutine(nameof(ReloadAfterWin));
            }
            if (purplescore >= winScore)
            {
                resultPanel.transform.localScale = new Vector3(1, 1, 1);
                resultText.text = "You Lose!";
                resultText.color = Color.red;
                StartCoroutine(nameof(ReloadAfterWin));
            }
        }
        m_ResetTimer += 1;
        if (m_ResetTimer >= MaxEnvironmentSteps && MaxEnvironmentSteps > 0)
        {
            m_BlueAgentGroup.GroupEpisodeInterrupted();
            m_PurpleAgentGroup.GroupEpisodeInterrupted();
            ResetScene();
        }
    }

    IEnumerator ReloadAfterWin()
    {
        yield return new WaitForSeconds(2f);
        SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex);
    }


    public void ResetBall()
    {
        var randomPosX = Random.Range(-2.5f, 2.5f);
        var randomPosZ = Random.Range(-2.5f, 2.5f);

        ball.transform.position = m_BallStartingPos + new Vector3(randomPosX, 0f, randomPosZ);
        ballRb.velocity = Vector3.zero;
        ballRb.angularVelocity = Vector3.zero;

    }

    public void GoalTouched(Team scoredTeam)
    {
        if (scoredTeam == Team.Blue)
        {
            m_BlueAgentGroup.AddGroupReward(1 - (float)m_ResetTimer / MaxEnvironmentSteps);
            m_PurpleAgentGroup.AddGroupReward(-1);
            if (gameObject.CompareTag("ScoreField"))
            {
                bluescore++;
                
            }
        }
        else
        {
            m_PurpleAgentGroup.AddGroupReward(1 - (float)m_ResetTimer / MaxEnvironmentSteps);
            m_BlueAgentGroup.AddGroupReward(-1);
            if (gameObject.CompareTag("ScoreField"))
            {
                purplescore++;
                
            }
        }
        m_PurpleAgentGroup.EndGroupEpisode();
        m_BlueAgentGroup.EndGroupEpisode();
        ResetScene();

    }

    public void BallTouched(Team touchedTeam)
    {
        if (touchedTeam == Team.Blue)
        {
            if (gameObject.CompareTag("ScoreField"))
                blueTouch++;
        }
        else
        {
            if (gameObject.CompareTag("ScoreField"))
                purpleTouch++;
        }
    }

    public void runningDis(Team runningTeam)
    {
        if (runningTeam == Team.Blue)
        {
            if (gameObject.CompareTag("ScoreField"))
                blueDis += 0.01;
                blueDis = Math.Round(blueDis, 3);
        }
        else
        {
            if (gameObject.CompareTag("ScoreField"))
                purpleDis += 0.01;
                purpleDis = Math.Round(purpleDis, 3); ;
        }
    }

    public void ResetScene()
    {
        m_ResetTimer = 0;

        //Reset Agents
        foreach (var item in AgentsList)
        {
            var randomPosX = Random.Range(-5f, 5f);
            var newStartPos = item.Agent.initialPos + new Vector3(randomPosX, 0f, 0f);
            var rot = item.Agent.rotSign * Random.Range(80.0f, 100.0f);
            var newRot = Quaternion.Euler(0, rot, 0);
            item.Agent.transform.SetPositionAndRotation(newStartPos, newRot);

            item.Rb.velocity = Vector3.zero;
            item.Rb.angularVelocity = Vector3.zero;
        }

        //Reset Ball
        ResetBall();
    }
}

