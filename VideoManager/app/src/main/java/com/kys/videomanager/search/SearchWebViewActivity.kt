package com.kys.videomanager.search
import com.kys.videomanager.R

import android.os.Bundle
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity

class SearchWebViewActivity : AppCompatActivity() {
    private lateinit var controller: SearchWebViewController

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_search_webview)
        controller = SearchWebViewController(this, findViewById(android.R.id.content))
        controller.start()

        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (controller.handleBack()) {
                    return
                } else {
                    isEnabled = false
                    onBackPressedDispatcher.onBackPressed()
                }
            }
        })
    }

    override fun onDestroy() {
        controller.destroy()
        super.onDestroy()
    }
}
