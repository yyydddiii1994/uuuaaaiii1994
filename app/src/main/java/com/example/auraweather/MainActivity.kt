package com.example.auraweather

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import androidx.compose.ui.unit.dp
import com.example.auraweather.ui.theme.AuraWeatherTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            AuraWeatherTheme {
                // A surface container using the 'background' color from the theme
                Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
                    WidgetShowcaseScreen()
                }
            }
        }
    }
}

@Composable
fun WidgetShowcaseScreen(modifier: Modifier = Modifier) {
    Column(modifier = modifier.padding(16.dp)) {
        Text(
            text = "Aura Weather Widgets",
            style = MaterialTheme.typography.headlineMedium
        )
        // This is where the list of widget previews will go.
        // For now, we'll just put a placeholder.
        Text(
            text = "Widget previews will be shown here.",
            modifier = Modifier.padding(top = 16.dp)
        )
    }
}

@Preview(showBackground = true)
@Composable
fun WidgetShowcaseScreenPreview() {
    AuraWeatherTheme {
        WidgetShowcaseScreen()
    }
}
