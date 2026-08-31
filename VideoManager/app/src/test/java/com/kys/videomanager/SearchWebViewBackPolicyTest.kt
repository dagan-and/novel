package com.kys.videomanager

import org.junit.Assert.assertEquals
import org.junit.Test

class SearchWebViewBackPolicyTest {
    @Test
    fun usesWebViewBackWhenNativeHistoryExists() {
        assertEquals(
            SearchWebViewBackAction.WEB_VIEW_BACK,
            SearchWebViewBackPolicy.resolve(nativeCanGoBack = true, clientSideHistoryDepth = 0)
        )
    }

    @Test
    fun usesWebViewBackWhenOnlyClientSideHistoryExists() {
        assertEquals(
            SearchWebViewBackAction.WEB_VIEW_BACK,
            SearchWebViewBackPolicy.resolve(nativeCanGoBack = false, clientSideHistoryDepth = 2)
        )
    }

    @Test
    fun leavesSearchWhenNoWebViewHistoryExists() {
        assertEquals(
            SearchWebViewBackAction.LEAVE_SEARCH,
            SearchWebViewBackPolicy.resolve(nativeCanGoBack = false, clientSideHistoryDepth = 0)
        )
    }
}
