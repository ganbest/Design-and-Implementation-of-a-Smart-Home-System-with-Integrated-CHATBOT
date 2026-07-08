#include <WiFi.h>
#include <HTTPClient.h>
#include <WebServer.h>
#include <TFT_eSPI.h>
#include <JPEGDEC.h>

// ── Cấu hình ─────────────────────────────────────────────────────────────────
const char* SSID      = "TEN_WIFI";
const char* PASSWORD  = "MAT_KHAU_WIFI";
const char* CAM_URL   = "http://192.168.1.38/capture";

// ── Khai báo ─────────────────────────────────────────────────────────────────
TFT_eSPI tft = TFT_eSPI();
JPEGDEC  jpeg;
WebServer server(80);

// ── JPEG callback — vẽ từng block pixel lên TFT ───────────────────────────
int jpegDraw(JPEGDRAW* pDraw) {
  tft.pushImage(pDraw->x, pDraw->y,
                pDraw->iWidth, pDraw->iHeight,
                pDraw->pPixels);
  return 1;
}

// ── Fetch ảnh từ ESP32-CAM và hiển thị ───────────────────────────────────
void fetchAndDisplay(String name) {
  HTTPClient http;
  http.begin(CAM_URL);
  http.setTimeout(5000);
  int code = http.GET();

  if (code == HTTP_CODE_OK) {
    WiFiClient* stream = http.getStreamPtr();
    int len = http.getSize();  // -1 nếu chunked transfer

    const size_t MAX_JPEG = 60000;
    uint8_t* buf = (uint8_t*) ps_malloc(MAX_JPEG);

    if (buf) {
      size_t totalRead = 0;

      if (len > 0) {
        // Content-Length biết trước
        size_t toRead = (len < (int)MAX_JPEG) ? len : MAX_JPEG;
        stream->readBytes(buf, toRead);
        totalRead = toRead;
      } else {
        // Chunked: đọc cho đến khi hết dữ liệu
        unsigned long t = millis();
        while ((http.connected() || stream->available()) && millis() - t < 5000) {
          if (stream->available()) {
            size_t n = stream->readBytes(buf + totalRead, MAX_JPEG - totalRead);
            totalRead += n;
            if (totalRead >= MAX_JPEG) break;
          } else {
            delay(1);
          }
        }
      }

      if (totalRead > 0) {
        tft.fillScreen(TFT_BLACK);

        if (jpeg.openRAM(buf, totalRead, jpegDraw)) {
          // RGB565_LITTLE_ENDIAN khớp với TFT_eSPI pushImage
          jpeg.setPixelType(RGB565_LITTLE_ENDIAN);
          jpeg.decode(0, 0, JPEG_SCALE_HALF);
          jpeg.close();
        }

        // Hiện tên bên dưới ảnh
        tft.fillRect(0, tft.height() - 20, tft.width(), 20, TFT_BLACK);
        tft.setTextColor(TFT_GREEN, TFT_BLACK);
        tft.setTextSize(1);
        tft.setCursor(4, tft.height() - 14);
        tft.print("CHAO " + name + "!");
      } else {
        tft.fillScreen(TFT_BLACK);
        tft.setTextColor(TFT_RED);
        tft.setCursor(4, 70);
        tft.print("Khong doc duoc!");
      }

      free(buf);
    }
  } else {
    tft.fillScreen(TFT_BLACK);
    tft.setTextColor(TFT_RED);
    tft.setCursor(4, 70);
    tft.print("Loi camera!");
  }
  http.end();
}

// ── HTTP handlers ─────────────────────────────────────────────────────────
void handleOpen() {
  String name = server.arg("name");
  if (name.isEmpty()) name = "BAN";
  fetchAndDisplay(name);
  server.send(200, "text/plain", "OK");
}

void handleAlert() {
  tft.fillScreen(TFT_RED);
  tft.setTextColor(TFT_WHITE, TFT_RED);
  tft.setTextSize(2);
  tft.setCursor(8, 55);
  tft.println("CANH");
  tft.setCursor(8, 80);
  tft.println("BAO!");
  tft.setTextSize(1);
  tft.setCursor(4, 115);
  tft.println("Khong nhan ra!");
  server.send(200, "text/plain", "OK");
}

void handleRoot() {
  server.send(200, "text/plain", "ESP32-S3 Display OK");
}

// ── Setup ─────────────────────────────────────────────────────────────────
void setup() {
  Serial.begin(115200);

  // Khởi động TFT
  tft.init();
  tft.setRotation(0);   // dọc 128x160
  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_WHITE);
  tft.setTextSize(1);
  tft.setCursor(4, 70);
  tft.print("Dang ket noi WiFi...");

  // Kết nối WiFi
  WiFi.begin(SSID, PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  String ip = WiFi.localIP().toString();
  Serial.println("\nIP: " + ip);

  tft.fillScreen(TFT_BLACK);
  tft.setTextColor(TFT_GREEN);
  tft.setCursor(4, 60);
  tft.println("WiFi OK!");
  tft.setTextColor(TFT_WHITE);
  tft.setCursor(4, 80);
  tft.println(ip);

  // Khởi động web server
  server.on("/",      handleRoot);
  server.on("/open",  handleOpen);
  server.on("/alert", handleAlert);
  server.begin();

  delay(1500);
  tft.fillScreen(TFT_BLACK);
  tft.setCursor(4, 70);
  tft.setTextColor(TFT_CYAN);
  tft.println("San sang...");
}

// ── Loop ─────────────────────────────────────────────────────────────────
void loop() {
  server.handleClient();
}
