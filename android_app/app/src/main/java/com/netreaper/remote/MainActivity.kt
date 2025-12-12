package com.netreaper.remote

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.lifecycle.viewmodel.compose.viewModel
import com.netreaper.remote.ui.theme.NetReaperRemoteTheme
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContent {
            NetReaperRemoteTheme {
                MainScreen()
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MainScreen(viewModel: NetReaperViewModel = viewModel()) {
    val tabs = listOf("SCAN", "RECON", "WIRELESS", "WEB")
    var selectedTabIndex by remember { mutableStateOf(0) }
    val scope = rememberCoroutineScope()

    Scaffold(
        topBar = { HUDPanel(viewModel) },
        containerColor = Color(0xFF050510)
    ) { padding ->
        Column(modifier = Modifier.padding(padding)) {
            TabRow(
                selectedTabIndex = selectedTabIndex,
                containerColor = Color(0xFF0e0b1f),
                contentColor = Color(0xFFc9d1ff)
            ) {
                tabs.forEachIndexed { index, title ->
                    Tab(
                        selected = selectedTabIndex == index,
                        onClick = { selectedTabIndex = index },
                        text = { Text(title, fontFamily = FontFamily.Monospace) },
                        selectedContentColor = Color(0xFF4b00ff),
                        unselectedContentColor = Color(0xFFc9d1ff)
                    )
                }
            }
            PairingPanel(viewModel)
            when (selectedTabIndex) {
                0 -> ScanTab(viewModel)
                1 -> ReconTab(viewModel)
                2 -> WirelessTab(viewModel)
                3 -> WebTab(viewModel)
            }
            Spacer(modifier = Modifier.weight(1f))
            OutputLog(viewModel)
        }
    }
}

@Composable
fun HUDPanel(viewModel: NetReaperViewModel) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color(0xFF090b1d))
            .padding(8.dp),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text("GRID STATUS: ${viewModel.status.value}", color = Color(0xFFc9d1ff), fontFamily = FontFamily.Monospace)
        Text("Cyber Pulse: ${viewModel.pulse}%", color = Color(0xFF00c6ff), fontFamily = FontFamily.Monospace)
        Text("Latency: ${viewModel.latency} ms", color = Color(0xFF562dff), fontFamily = FontFamily.Monospace)
    }
}

@Composable
fun ScanTab(viewModel: NetReaperViewModel) {
    Column(modifier = Modifier.padding(16.dp)) {
        OutlinedTextField(
            value = viewModel.target.value,
            onValueChange = { viewModel.target.value = it },
            label = { Text("Target") },
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(modifier = Modifier.height(8.dp))
        Row {
            Button(onClick = { viewModel.executeCommand("nmap -T4 -F ${viewModel.target.value}") }) {
                Text("Quick Scan")
            }
            Spacer(modifier = Modifier.width(8.dp))
            Button(onClick = { viewModel.executeCommand("sudo nmap -sS -sV -A -p- ${viewModel.target.value}") }) {
                Text("Full Scan")
            }
        }
        // Add more buttons as per GUI
    }
}

@Composable
fun ReconTab(viewModel: NetReaperViewModel) {
    // Similar to ScanTab, with recon buttons
    Column(modifier = Modifier.padding(16.dp)) {
        OutlinedTextField(
            value = viewModel.target.value,
            onValueChange = { viewModel.target.value = it },
            label = { Text("Subnet/host") },
            modifier = Modifier.fillMaxWidth()
        )
        Button(onClick = { viewModel.executeCommand("nmap -sn ${viewModel.target.value}") }) {
            Text("Ping Sweep")
        }
    }
}

@Composable
fun WirelessTab(viewModel: NetReaperViewModel) {
    // Wireless controls
    Column(modifier = Modifier.padding(16.dp)) {
        OutlinedTextField(
            value = viewModel.interface.value,
            onValueChange = { viewModel.interface.value = it },
            label = { Text("Wireless Interface") },
            modifier = Modifier.fillMaxWidth()
        )
        Button(onClick = { viewModel.executeCommand("sudo airmon-ng start ${viewModel.interface.value}") }) {
            Text("Enable Monitor")
        }
    }
}

@Composable
fun WebTab(viewModel: NetReaperViewModel) {
    // Web tools
    Column(modifier = Modifier.padding(16.dp)) {
        OutlinedTextField(
            value = viewModel.target.value,
            onValueChange = { viewModel.target.value = it },
            label = { Text("URL/Domain") },
            modifier = Modifier.fillMaxWidth()
        )
        Button(onClick = { viewModel.executeCommand("nikto -host ${viewModel.target.value}") }) {
            Text("Nikto Scan")
        }
    }
}

@Composable
fun OutputLog(viewModel: NetReaperViewModel) {
    LazyColumn(
        modifier = Modifier
            .fillMaxWidth()
            .height(200.dp)
            .background(Color(0xFF03030a))
            .padding(8.dp)
    ) {
        items(viewModel.log.value) { line ->
            Text(line, color = Color(0xFF00c6ff), fontFamily = FontFamily.Monospace)
        }
    }
}

@Composable
fun PairingPanel(viewModel: NetReaperViewModel) {
    Column(
        modifier = Modifier
            .fillMaxWidth()
            .padding(12.dp)
            .background(
                brush = Brush.linearGradient(
                    listOf(Color(0xFF070716), Color(0xFF11102a))
                ),
                shape = RoundedCornerShape(16.dp)
            )
            .padding(16.dp)
    ) {
        Text(
            "Device Pairing & Connections",
            fontWeight = FontWeight.Bold,
            color = Color(0xFFc9d1ff),
            fontSize = 14.sp
        )
        Spacer(modifier = Modifier.height(8.dp))
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            StatusCard(
                title = "Remote Device",
                paired = viewModel.remotePaired.value,
                badgeText = viewModel.connectionState.value.name,
                onAction = { viewModel.pairDevice() },
                actionLabel = if (viewModel.remotePaired.value) "Re-Pair" else "Pair Device"
            )
            StatusCard(
                title = "GUI Application",
                paired = viewModel.guiPaired.value,
                badgeText = viewModel.connectionState.value.name,
                onAction = { viewModel.pairGui() },
                actionLabel = if (viewModel.guiPaired.value) "Refresh Pairing" else "Pair GUI"
            )
        }
        Spacer(modifier = Modifier.height(12.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            OutlinedTextField(
                value = viewModel.hostInput.value,
                onValueChange = { viewModel.hostInput.value = it },
                label = { Text("Host", color = Color(0xFFc9d1ff)) },
                modifier = Modifier.weight(1f),
                colors = TextFieldDefaults.outlinedTextFieldColors(
                    textColor = Color(0xFFc9d1ff),
                    focusedBorderColor = Color(0xFF6f00ff),
                    unfocusedBorderColor = Color(0xFF312162)
                )
            )
            Spacer(modifier = Modifier.width(8.dp))
            OutlinedTextField(
                value = viewModel.passwordInput.value,
                onValueChange = { viewModel.passwordInput.value = it },
                label = { Text("Password", color = Color(0xFFc9d1ff)) },
                modifier = Modifier.weight(1f),
                colors = TextFieldDefaults.outlinedTextFieldColors(
                    textColor = Color(0xFFc9d1ff),
                    focusedBorderColor = Color(0xFF6f00ff),
                    unfocusedBorderColor = Color(0xFF312162)
                )
            )
        }
        Spacer(modifier = Modifier.height(8.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Button(
                onClick = { viewModel.connect(viewModel.hostInput.value, viewModel.passwordInput.value) },
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF4b00ff))
            ) {
                Text("Connect", color = Color.White)
            }
            Button(
                onClick = { viewModel.disconnect() },
                colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFc900ff))
            ) {
                Text("Disconnect", color = Color.White)
            }
            ConnectionBadge(state = viewModel.connectionState.value)
        }
        Spacer(modifier = Modifier.height(8.dp))
        LazyColumn(modifier = Modifier.height(80.dp)) {
            items(viewModel.connectionMessages.toList()) { message ->
                Text(message, fontSize = 10.sp, color = Color(0xFF56ffea))
            }
        }
        Spacer(modifier = Modifier.height(8.dp))
        LazyColumn(modifier = Modifier.height(80.dp)) {
            items(viewModel.pairingFeedback.toList()) { message ->
                Text(message, fontSize = 10.sp, color = Color(0xFFea76ff))
            }
        }
    }
}

@Composable
fun StatusCard(
    title: String,
    paired: Boolean,
    badgeText: String,
    onAction: () -> Unit,
    actionLabel: String
) {
    Card(
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF130f2c)),
        modifier = Modifier
            .weight(1f)
            .border(
                width = 1.dp,
                color = if (paired) Color(0xFF00ff94) else Color(0xFF5645ff),
                shape = RoundedCornerShape(12.dp)
            )
    ) {
        Column(modifier = Modifier.padding(12.dp)) {
            Text(title, fontWeight = FontWeight.Bold, color = Color(0xFFc9d1ff))
            Spacer(modifier = Modifier.height(4.dp))
            Text("Status: ${if (paired) "Paired" else "Not paired"}", color = Color.White, fontSize = 12.sp)
            Spacer(modifier = Modifier.height(6.dp))
            Row(
                horizontalArrangement = Arrangement.SpaceBetween,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text(badgeText, color = Color(0xFF00c6ff), fontSize = 12.sp)
                Button(
                    onClick = onAction,
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF4b00ff))
                ) {
                    Text(actionLabel, fontSize = 10.sp, color = Color.White)
                }
            }
        }
    }
}

@Composable
fun ConnectionBadge(state: ConnectionState) {
    val color = when (state) {
        ConnectionState.CONNECTED -> Color(0xFF02ff6a)
        ConnectionState.CONNECTING -> Color(0xFFf5c23d)
        ConnectionState.DISCONNECTED -> Color(0xFFff3a3a)
    }
    Text(
        state.name,
        color = color,
        modifier = Modifier
            .background(color.copy(alpha = 0.2f), shape = RoundedCornerShape(8.dp))
            .padding(horizontal = 8.dp, vertical = 4.dp),
        fontSize = 12.sp,
        fontWeight = FontWeight.SemiBold
    )
}
