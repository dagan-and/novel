package com.kys.videomanager

enum class SearchWebViewBackAction {
    WEB_VIEW_BACK,
    LEAVE_SEARCH
}

object SearchWebViewBackPolicy {
    fun resolve(nativeCanGoBack: Boolean, clientSideHistoryDepth: Int): SearchWebViewBackAction =
        if (clientSideHistoryDepth > 0 || nativeCanGoBack) {
            SearchWebViewBackAction.WEB_VIEW_BACK
        } else {
            SearchWebViewBackAction.LEAVE_SEARCH
        }
}
