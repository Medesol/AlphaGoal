using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Serialization;

public class FaceToCamera : MonoBehaviour
{

    public Camera myCamera;
    // Update is called once per frame
    void Start()
    {
        myCamera = Camera.main;
    }
    
    void Update()
    {
        var rotation = myCamera.transform.rotation;
        transform.LookAt(transform.position+rotation*Vector3.back, 
            rotation*Vector3.up);
    }
}
