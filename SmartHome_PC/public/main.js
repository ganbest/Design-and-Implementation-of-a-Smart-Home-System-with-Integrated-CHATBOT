// Dòng này cần phải có ở đầu file
const { app, BrowserWindow } = require('electron')
// THÊM DÒNG NÀY: Dùng path để xử lý đường dẫn file chuẩn
const path = require('path') 

function createWindow () {
  // Tạo cửa sổ trình duyệt
  const win = new BrowserWindow({
    width: 1200,
    height: 800,
    // SỬA DÒNG NÀY: Dùng path.join(__dirname, ...) để lấy đường dẫn file chuẩn
    // Đảm bảo file ảnh 'logo.ico' nằm cùng thư mục với file main.js nhé!
    icon: path.join(__dirname, 'public/logoh.ico'), 
    webPreferences: {
      nodeIntegration: true
    }
  })

  // load file index.html của bạn
  win.loadFile('public/index.html')

  // Mở DevTools (nếu cần)
  // win.webContents.openDevTools()
}

// Gọi hàm createWindow khi app sẵn sàng
app.whenReady().then(createWindow)