package com.kys.videomanager.update

import android.content.Context
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import android.net.NetworkRequest

/**
 * 앱 전체 사용에 필요한 실제 인터넷 연결 여부를 확인하고, 끊겨 있으면 연결될 때까지 기다린다.
 * NET_CAPABILITY_VALIDATED까지 확인하므로 와이파이에 붙어 있어도 실제 인터넷이 안 되면(캡티브 포털 등)
 * 연결된 것으로 보지 않는다.
 */
class NetworkConnectivityGate(private val context: Context) {

    fun isConnected(): Boolean {
        val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as? ConnectivityManager
            ?: return false
        val network = connectivityManager.activeNetwork ?: return false
        val capabilities = connectivityManager.getNetworkCapabilities(network) ?: return false
        return capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) &&
            capabilities.hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED)
    }

    fun awaitConnectivity(onAvailable: () -> Unit): ConnectivityManager.NetworkCallback {
        val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val request = NetworkRequest.Builder()
            .addCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET)
            .addCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED)
            .build()
        val callback = object : ConnectivityManager.NetworkCallback() {
            override fun onAvailable(network: Network) {
                onAvailable()
            }
        }
        connectivityManager.registerNetworkCallback(request, callback)
        return callback
    }

    fun stopAwaiting(callback: ConnectivityManager.NetworkCallback) {
        val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as? ConnectivityManager
            ?: return
        runCatching { connectivityManager.unregisterNetworkCallback(callback) }
    }
}
