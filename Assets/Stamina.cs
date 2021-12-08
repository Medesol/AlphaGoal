using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

public class Stamina : MonoBehaviour
{
    // Start is called before the first frame update
    private Rigidbody agentRb;
    private Slider slider;
    private float regSpeed = 0.08f; // 体力恢复速度
    private float decreaseSpeed = 0.02f; // 体力消耗速度
    private Image fill;
    void Start()
    {
        agentRb = GetComponent<Rigidbody>();
        slider = GetComponentInChildren<Slider>();
        fill = slider.transform.GetChild(1).GetChild(0).GetComponent<Image>();
        if (slider != null)
        {
            slider.value = 1f;
        }
    }

    private void Decrease()
    {
        // 根据当前速度的模消耗体力
        slider.value = Math.Max(slider.minValue,
            slider.value - decreaseSpeed * agentRb.velocity.magnitude * Time.deltaTime);
    }

    private void Regeneration()
    {
        // 让体力稳定恢复但不能超过最大值
        slider.value = Math.Min(slider.maxValue, slider.value + regSpeed * Time.deltaTime);
    }

    private void ChangeColor()
    {
        float staminaRatio = slider.value / slider.maxValue;
        if (staminaRatio > 0.3f && staminaRatio < 0.6f)
        {
            fill.color = Color.yellow;
        } else if (staminaRatio > 0f && staminaRatio < 0.3f)
        {
            fill.color = Color.red;
        }
        else
        {
            fill.color = Color.green;
        }
    }
    // Update is called once per frame
    void Update()
    {
        Decrease();
        Regeneration();
        ChangeColor();
    }
}
