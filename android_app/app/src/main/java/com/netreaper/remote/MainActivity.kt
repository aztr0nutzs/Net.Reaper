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
    val status by viewModel.status.collectAsState()
    val pulse by viewModel.pulse.collectAsState()
    val latency by viewModel.latency.collectAsState()

    Row(
        modifier = Modifier
            .fillMaxWidth()
            .background(Color(0xFF090b1d))
            .padding(8.dp),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text("GRID STATUS: $status", color = Color(0xFFc9d1ff), fontFamily = FontFamily.Monospace)
        Text("Cyber Pulse: $pulse%", color = Color(0xFF00c6ff), fontFamily = FontFamily.Monospace)
        Text("Latency: $latency ms", color = Color(0xFF562dff), fontFamily = FontFamily.Monospace)
    }
}

@Composable
fun ScanTab(viewModel: NetReaperViewModel) {
    val target by viewModel.target.collectAsState()

    Column(modifier = Modifier.padding(16.dp)) {
        OutlinedTextField(
            value = target,
            onValueChange = { viewModel.setTarget(it) },
            label = { Text("Target") },
            modifier = Modifier.fillMaxWidth()
        )
        Spacer(modifier = Modifier.height(8.dp))
        Row {
            Button(onClick = { viewModel.executeCommand("nmap -T4 -F $target") }) {
                Text("Quick Scan")
            }
            Spacer(modifier = Modifier.width(8.dp))
            Button(onClick = { viewModel.executeCommand("sudo nmap -sS -sV -A -p- $target") }) {
                Text("Full Scan")
            }
        }
        // Add more buttons as per GUI
    }
}

@Composable
fun ReconTab(viewModel: NetReaperViewModel) {
    val target by viewModel.target.collectAsState()

    // Similar to ScanTab, with recon buttons
    Column(modifier = Modifier.padding(16.dp)) {
        OutlinedTextField(
            value = target,
            onValueChange = { viewModel.setTarget(it) },
            label = { Text("Subnet/host") },
            modifier = Modifier.fillMaxWidth()
        )
        Button(onClick = { viewModel.executeCommand("nmap -sn $target") }) {
            Text("Ping Sweep")
        }
    }
}

@Composable
fun WirelessTab(viewModel: NetReaperViewModel) {
    val networkInterface by viewModel.networkInterface.collectAsState()

    // Wireless controls
    Column(modifier = Modifier.padding(16.dp)) {
        OutlinedTextField(
            value = networkInterface,
            onValueChange = { viewModel.setNetworkInterface(it) },
            label = { Text("Wireless Interface") },
            modifier = Modifier.fillMaxWidth()
        )
        Button(onClick = { viewModel.executeCommand("sudo airmon-ng start $networkInterface") }) {
            Text("Enable Monitor")
        }
    }
}

@Composable
fun WebTab(viewModel: NetReaperViewModel) {
    val target by viewModel.target.collectAsState()

    // Web tools
    Column(modifier = Modifier.padding(16.dp)) {
        OutlinedTextField(
            value = target,
            onValueChange = { viewModel.setTarget(it) },
            label = { Text("URL/Domain") },
            modifier = Modifier.fillMaxWidth()
        )
        Button(onClick = { viewModel.executeCommand("nikto -host $target") }) {
            Text("Nikto Scan")
        }
    }
}

@Composable
fun OutputLog(viewModel: NetReaperViewModel) {
    val log by viewModel.log.collectAsState()

    LazyColumn(
        modifier = Modifier
            .fillMaxWidth()
            .height(200.dp)
            .background(Color(0xFF03030a))
            .padding(8.dp)
    ) {
        items(log) { line ->
            Text(line, color = Color(0xFF00c6ff), fontFamily = FontFamily.Monospace)
        }
    }
}

@Composable
fun PairingPanel(viewModel: NetReaperViewModel) {
    val remotePaired by viewModel.remotePaired.collectAsState()
    val guiPaired by viewModel.guiPaired.collectAsState()
    val connectionState by viewModel.connectionState.collectAsState()
    val hostInput by viewModel.hostInput.collectAsState()
    val passwordInput by viewModel.passwordInput.collectAsState()
    val connectionMessages by viewModel.connectionMessages.collectAsState()
    val pairingFeedback by viewModel.pairingFeedback.collectAsState()

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
                paired = remotePaired,
                badgeText = connectionState.name,
                onAction = { viewModel.pairDevice() },
                actionLabel = if (remotePaired) "Re-Pair" else "Pair Device",
                modifier = Modifier.weight(1f)
            )
            StatusCard(
                title = "GUI Application",
                paired = guiPaired,
                badgeText = connectionState.name,
                onAction = { viewModel.pairGui() },
                actionLabel = if (guiPaired) "Refresh Pairing" else "Pair GUI",
                modifier = Modifier.weight(1f)
            )
        }
        Spacer(modifier = Modifier.height(12.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            OutlinedTextField(
                value = hostInput,
                onValueChange = { viewModel.setHostInput(it) },
                label = { Text("Host", color = Color(0xFFc9d1ff)) },
                modifier = Modifier.weight(1f),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = Color(0xFF6f00ff),
                    unfocusedBorderColor = Color(0xFF312162)
                )
            )
            Spacer(modifier = Modifier.width(8.dp))
            OutlinedTextField(
                value = passwordInput,
                onValueChange = { viewModel.setPasswordInput(it) },
                label = { Text("Password", color = Color(0xFFc9d1ff)) },
                modifier = Modifier.weight(1f),
                colors = OutlinedTextFieldDefaults.colors(
                    focusedBorderColor = Color(0xFF6f00ff),
                    unfocusedBorderColor = Color(0xFF312162)
                )
            )
        }
        Spacer(modifier = Modifier.height(8.dp))
        Row(horizontalArrangement = Arrangement.spacedBy(12.dp)) {
            Button(
                onClick = { viewModel.connect(hostInput, passwordInput) },
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
            ConnectionBadge(state = connectionState)
        }
        Spacer(modifier = Modifier.height(8.dp))
        LazyColumn(modifier = Modifier.height(80.dp)) {
            items(connectionMessages) { message ->
                Text(message, fontSize = 10.sp, color = Color(0xFF56ffea))
            }
        }
        Spacer(modifier = Modifier.height(8.dp))
        LazyColumn(modifier = Modifier.height(80.dp)) {
            items(pairingFeedback) { message ->
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
    actionLabel: String,
    modifier: Modifier = Modifier
) {
    Card(
        shape = RoundedCornerShape(12.dp),
        colors = CardDefaults.cardColors(containerColor = Color(0xFF130f2c)),
        modifier = modifier
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
