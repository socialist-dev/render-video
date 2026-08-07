const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
  // Cập nhật cấu hình launch để chạy được trên GitHub Actions
  const browser = await puppeteer.launch({ 
    headless: "new",
    args: [
      '--no-sandbox', 
      '--disable-setuid-sandbox',
      '--disable-dev-shm-usage',
      '--disable-accelerated-2d-canvas',
      '--no-first-run',
      '--no-zygote',
      '--single-process',
      '--disable-gpu'
    ]
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1080, height: 1920 });

  // Đọc file HTML
  if (!fs.existsSync('ui.html')) {
    console.error("Error: ui.html not found!");
    process.exit(1);
  }
  let html = fs.readFileSync('ui.html', 'utf8');

  // Thay thế tiêu đề từ tham số truyền vào
  const title = process.argv[2] || "Default Title";
  html = html.replace("TITLE_PLACEHOLDER", title);
  
  await page.setContent(html);

  // Đợi một chút để đảm bảo font chữ và layout đã render xong
  await new Promise(r => setTimeout(r, 500));

  // Tính tọa độ vùng đỏ (khung chứa video)
  const rect = await page.evaluate(() => {
    const el = document.querySelector('.container__content');
    if (!el) return null;
    const r = el.getBoundingClientRect();
    return { 
      x: Math.round(r.left), 
      y: Math.round(r.top), 
      w: Math.round(r.width), 
      h: Math.round(r.height) 
    };
  });

  if (!rect) {
    console.error("Error: Could not find .container__content in HTML");
    await browser.close();
    process.exit(1);
  }

  // Chụp ảnh PNG (trong suốt nền)
  await page.screenshot({ path: 'cover.png', omitBackground: true });
  
  // Lưu tọa độ để file YAML (FFmpeg) đọc được
  fs.writeFileSync('coords.txt', `${rect.x}:${rect.y}:${rect.w}:${rect.h}`);
  
  console.log(`Rendered UI successfully.`);
  console.log(`Coords found: X=${rect.x}, Y=${rect.y}, W=${rect.w}, H=${rect.h}`);
  
  await browser.close();
})();
