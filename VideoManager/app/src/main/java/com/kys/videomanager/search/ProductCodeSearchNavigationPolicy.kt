package com.kys.videomanager.search
import com.kys.videomanager.main.MainScreenUiModel

enum class ProductCodeSearchNavigation {
    EXTERNAL_BROWSER
}

data class ProductCodeSearchNavigationState(
    val destination: ProductCodeSearchNavigation,
    val url: String
)

object ProductCodeSearchNavigationPolicy {
    fun resolve(): ProductCodeSearchNavigationState =
        ProductCodeSearchNavigationState(
            destination = ProductCodeSearchNavigation.EXTERNAL_BROWSER,
            url = MainScreenUiModel.productCodeHomeUrl
        )
}
