#include <WiFi.h>
#include <FirebaseESP32.h>
#include <DHT.h>
#include <time.h>

// ================= WIFI =================
#define WIFI_SSID     "Sang"
#define WIFI_PASSWORD "0905846609"

// ================= FIREBASE =================
#define FIREBASE_HOST "monitoremp-f1080-default-rtdb.asia-southeast1.firebasedatabase.app"
#define FIREBASE_AUTH "CUdQQzahScE9j9aIHVOFlS7OMvQVwLp9xJyqbz4R"

// ================= DHT =================
#define DHT_PIN 5          // GPIO5
#define DHT_TYPE DHT11
#define SEND_INTERVAL 5000

// ================= NTP =================
#define NTP_SERVER "pool.ntp.org"
#define GMT_OFFSET_SEC 25200
#define DAYLIGHT_OFFSET 0

DHT dht(DHT_PIN, DHT_TYPE);

FirebaseData fbData;
FirebaseAuth auth;
FirebaseConfig config;

unsigned long lastSendTime = 0;
int readingCount = 0;

// ============================================================
void setup() {
  Serial.begin(115200);
  Serial.println("\n=== ESP32 DHT Firebase Monitor ===");

  dht.begin();
  delay(1000);

  connectWiFi();

  // Đồng bộ thời gian
  configTime(GMT_OFFSET_SEC, DAYLIGHT_OFFSET, NTP_SERVER);
  Serial.print("Đang lấy thời gian NTP");

  struct tm timeinfo;
  while (!getLocalTime(&timeinfo)) {
    Serial.print(".");
    delay(500);
  }
  Serial.println(" OK");

  // Firebase
  config.host = FIREBASE_HOST;
  config.signer.tokens.legacy_token = FIREBASE_AUTH;

  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);

  Serial.println("Firebase đã kết nối!");
}

// ============================================================
void loop() {
  unsigned long now = millis();

  if (now - lastSendTime >= SEND_INTERVAL) {
    lastSendTime = now;
    readAndSendData();
  }

  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi mất kết nối! Đang kết nối lại...");
    connectWiFi();
  }
}

// ============================================================
void readAndSendData() {
  float temperature = dht.readTemperature();
  float humidity = dht.readHumidity();

  if (isnan(temperature) || isnan(humidity)) {
    Serial.println("[LỖI] Không đọc được DHT!");
    return;
  }

  float heatIndex = dht.computeHeatIndex(temperature, humidity, false);
  readingCount++;

  Serial.printf("\n--- Lần đọc #%d ---\n", readingCount);
  Serial.printf("Nhiệt độ : %.1f°C\n", temperature);
  Serial.printf("Độ ẩm    : %.1f%%\n", humidity);
  Serial.printf("Chỉ số nhiệt: %.1f°C\n", heatIndex);

  // Timestamp
  struct tm timeinfo;
  char timestamp[25];

  if (getLocalTime(&timeinfo)) {
    strftime(timestamp, sizeof(timestamp), "%Y-%m-%d %H:%M:%S", &timeinfo);
  } else {
    strcpy(timestamp, "unknown");
  }

  FirebaseJson json;
  json.set("temperature", temperature);
  json.set("humidity", humidity);
  json.set("heat_index", heatIndex);
  json.set("timestamp", timestamp);
  json.set("reading_count", readingCount);

  // ===== Latest =====
  if (Firebase.setJSON(fbData, "/sensor_data/latest", json)) {
    Serial.println("[Firebase] latest OK");
  } else {
    Serial.println("[Firebase] latest lỗi: " + fbData.errorReason());
  }

  // ===== History (giữ tối đa 100 bản ghi) =====
  String histPath = "/sensor_data/history/" + String(readingCount);

  if (Firebase.setJSON(fbData, histPath, json)) {
    Serial.println("[Firebase] history OK");
  } else {
    Serial.println("[Firebase] history lỗi: " + fbData.errorReason());
  }

  // Xóa bản ghi cũ
  if (readingCount > 100) {
    String oldPath = "/sensor_data/history/" + String(readingCount - 100);
    Firebase.deleteNode(fbData, oldPath);
  }
}

// ============================================================
void connectWiFi() {
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.print("Đang kết nối WiFi");

  int retries = 0;

  while (WiFi.status() != WL_CONNECTED && retries < 30) {
    delay(500);
    Serial.print(".");
    retries++;
  }

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi đã kết nối!");
    Serial.print("IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nKhông kết nối được WiFi!");
    ESP.restart();
  }
}