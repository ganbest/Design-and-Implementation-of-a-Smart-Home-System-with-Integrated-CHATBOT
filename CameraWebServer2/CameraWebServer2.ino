#include <Arduino.h>
#include "esp_camera.h"
#include <WiFi.h>
#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ST7735.h>
#include <JPEGDEC.h>

#define TFT_CLK  42   // SCLK
#define TFT_SDA  41   // MOSI
#define TFT_CS    2
#define TFT_RS    1   // DC
#define TFT_RST  21

// HARDWARE SPI — nhanh gap nhieu lan software SPI -> video muot
// Dung global SPI object, remap chan qua GPIO matrix cua ESP32-S3
Adafruit_ST7735 tft = Adafruit_ST7735(&SPI, TFT_CS, TFT_RS, TFT_RST);
JPEGDEC jpeg;

static volatile bool g_videoMode = true;
static uint32_t      g_resumeAt  = 0;

static int jpegDraw(JPEGDRAW* pDraw) {
  int16_t x = pDraw->x, y = pDraw->y;
  int16_t w = pDraw->iWidth, h = pDraw->iHeight;
  if (x >= tft.width() || y >= tft.height()) return 1;
  int16_t clipW = min((int16_t)(tft.width()  - x), w);
  int16_t clipH = min((int16_t)(tft.height() - y), h);
  tft.startWrite();
  for (int16_t row = 0; row < clipH; row++) {
    tft.setAddrWindow(x, y + row, clipW, 1);
    tft.writePixels(pDraw->pPixels + row * w, clipW);
  }
  tft.endWrite();
  return 1;
}

// Goi tu app_httpd.cpp (stream_handler) — dung ke frame web vua chup
// Throttle: chi ve TFT moi ~150ms de khong lam cham web stream
void displayLiveFrame(const uint8_t* buf, size_t len) {
  if (!g_videoMode) {
    if (millis() >= g_resumeAt) g_videoMode = true;
    else return;
  }
  if (jpeg.openRAM((uint8_t*)buf, len, jpegDraw)) {
    jpeg.setPixelType(RGB565_LITTLE_ENDIAN);
    jpeg.decode(0, 0, JPEG_SCALE_HALF);
    jpeg.close();
  }
}

void displayFace(const uint8_t* buf, size_t len, const char* name) {
  g_videoMode = false;
  g_resumeAt  = millis() + 5000;
  tft.fillScreen(ST77XX_BLACK);
  if (jpeg.openRAM((uint8_t*)buf, len, jpegDraw)) {
    jpeg.setPixelType(RGB565_LITTLE_ENDIAN);
    jpeg.decode(0, 0, JPEG_SCALE_HALF);
    jpeg.close();
  }
  tft.fillRect(0, tft.height() - 20, tft.width(), 20, ST77XX_BLACK);
  tft.setTextColor(ST77XX_GREEN);
  tft.setTextSize(1);
  tft.setCursor(4, tft.height() - 14);
  tft.printf("CHAO %s!", name);
  Serial.printf("[TFT] CHAO %s!\n", name);
}

void displayAlert() {
  g_videoMode = false;
  g_resumeAt  = millis() + 5000;
  tft.fillScreen(ST77XX_RED);
  tft.setTextColor(ST77XX_WHITE);
  tft.setTextSize(2);
  tft.setCursor(8, 40);  tft.println("CANH");
  tft.setCursor(8, 65);  tft.println("BAO!");
  tft.setTextSize(1);
  tft.setCursor(4, 100); tft.println("Khong nhan ra!");
  Serial.println("[TFT] CANH BAO!");
}

void displayTest() {
  g_videoMode = false;
  g_resumeAt  = millis() + 5000;
  int16_t w = tft.width(), h = tft.height();
  tft.fillRect(0,   0,   w/2, h/2, ST77XX_RED);
  tft.fillRect(w/2, 0,   w/2, h/2, ST77XX_GREEN);
  tft.fillRect(0,   h/2, w/2, h/2, ST77XX_BLUE);
  tft.fillRect(w/2, h/2, w/2, h/2, ST77XX_WHITE);
  tft.setTextColor(ST77XX_BLACK);
  tft.setTextSize(1);
  tft.setCursor(w/2 - 12, h/2 - 4);
  tft.print("TEST");
}

#include "board_config.h"

const char *ssid     = "Tanngu";
const char *password = "12346777";

void startCameraServer();
void setupLedFlash();

void setup() {
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();

  // Khoi tao hardware SPI voi dung chan: SCLK=42, MOSI=41 (MISO=-1 vi man hinh chi ghi)
  SPI.begin(TFT_CLK, -1, TFT_SDA, TFT_CS);
  tft.initR(INITR_BLACKTAB);
  tft.setRotation(1);
  tft.fillScreen(ST77XX_BLACK);
  tft.setTextColor(ST77XX_YELLOW);
  tft.setTextSize(1);
  tft.setCursor(4, 4);
  tft.println("Khoi dong...");

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = Y2_GPIO_NUM;
  config.pin_d1       = Y3_GPIO_NUM;
  config.pin_d2       = Y4_GPIO_NUM;
  config.pin_d3       = Y5_GPIO_NUM;
  config.pin_d4       = Y6_GPIO_NUM;
  config.pin_d5       = Y7_GPIO_NUM;
  config.pin_d6       = Y8_GPIO_NUM;
  config.pin_d7       = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.frame_size   = FRAMESIZE_UXGA;
  config.pixel_format = PIXFORMAT_JPEG;
  config.grab_mode    = CAMERA_GRAB_WHEN_EMPTY;
  config.fb_location  = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 12;
  config.fb_count     = 1;

  if (config.pixel_format == PIXFORMAT_JPEG) {
    if (psramFound()) {
      config.jpeg_quality = 10;
      config.fb_count     = 2;
      config.grab_mode    = CAMERA_GRAB_LATEST;
    } else {
      config.frame_size  = FRAMESIZE_SVGA;
      config.fb_location = CAMERA_FB_IN_DRAM;
    }
  } else {
    config.frame_size = FRAMESIZE_240X240;
#if CONFIG_IDF_TARGET_ESP32S3
    config.fb_count = 2;
#endif
  }

#if defined(CAMERA_MODEL_ESP_EYE)
  pinMode(13, INPUT_PULLUP);
  pinMode(14, INPUT_PULLUP);
#endif

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed 0x%x\n", err);
    tft.fillScreen(ST77XX_RED);
    tft.setCursor(4, 4); tft.println("CAM FAILED");
    return;
  }

  sensor_t *s = esp_camera_sensor_get();
  if (s->id.PID == OV3660_PID) {
    s->set_vflip(s, 1);
    s->set_brightness(s, 1);
    s->set_saturation(s, -2);
  }
  if (config.pixel_format == PIXFORMAT_JPEG) {
    s->set_framesize(s, FRAMESIZE_QVGA);
  }

#if defined(CAMERA_MODEL_M5STACK_WIDE) || defined(CAMERA_MODEL_M5STACK_ESP32CAM)
  s->set_vflip(s, 1);
  s->set_hmirror(s, 1);
#endif
#if defined(CAMERA_MODEL_ESP32S3_EYE)
  s->set_vflip(s, 1);
#endif
#if defined(LED_GPIO_NUM)
  setupLedFlash();
#endif

  WiFi.begin(ssid, password);
  WiFi.setSleep(false);
  Serial.print("WiFi connecting");
  uint32_t t0 = millis();
  while (WiFi.status() != WL_CONNECTED) {
    if (millis() - t0 > 30000) {
      Serial.println("\nWiFi timeout, restarting...");
      tft.fillScreen(ST77XX_RED);
      tft.setCursor(4, 4); tft.println("WiFi FAIL");
      delay(2000);
      ESP.restart();
    }
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected");

  startCameraServer();

  String ip = WiFi.localIP().toString();
  Serial.printf("Camera Ready! http://%s\n", ip.c_str());

  tft.fillScreen(ST77XX_BLACK);
  tft.setTextColor(ST77XX_GREEN);
  tft.setTextSize(1);
  tft.setCursor(4, 20); tft.println("San sang!");
  tft.setTextColor(ST77XX_WHITE);
  tft.setCursor(4, 40); tft.println(ip.c_str());

  delay(2000);
  g_videoMode = true;
}

// loop() KHONG chup frame nua — TFT ve tu frame cua web stream (displayLiveFrame)
void loop() {
  delay(1000);
}
