package com.kys.videomanager

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import com.kys.videomanager.R

class DownloadStatusActivity : AppCompatActivity() {
    private lateinit var controller: DownloadStatusController

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_download_status)
        controller = DownloadStatusController(this, findViewById(android.R.id.content))
        controller.start()
    }

    override fun onStart() {
        super.onStart()
        controller.resume()
    }

    override fun onStop() {
        controller.pause()
        super.onStop()
    }
}
