const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
  let browser;
  try {
    browser = await puppeteer.launch({
      // Dùng chế độ mới nhất của Puppeteer
      headless: "shell", 
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
        '--disable-dev-shm-usage',
        '--disable-gpu',
      ]
    });

    const page = await browser.newPage();
    await page.setViewport({ width: 1080, height: 1920 });

    // Đọc HTML
    if (!fs.existsSync('ui.html')) throw new Error("ui.html missing");
    let html = fs.readFileSync('ui.html', 'utf8');

    // Thay Title
    const title = process.argv[2] || "Default Title";
    html = html.replace("TITLE_PLACEHOLDER", title);
    
    await page.setContent(html, { waitUntil: 'networkidle0' });

    // Lấy tọa độ vùng đỏ
    const rect = await page.evaluate(() => {
      const el = document.querySelector('.container__content');
      if (!el) return null;
      const r = el.getBoundingClientRect();
      return { x: Math.round(r.left), y: Math.round(r.top), w: Math.round(r.width), h: Math.round(r.height) };
    });

    if (!rect) throw new Error("Could not find .container__content");

    // Chụp ảnh
    await page.screenshot({ path: 'cover.png', omitBackground: true });
    
    // Lưu tọa độ
    fs.writeFileSync('coords.txt', `${rect.x}:${rect.y}:${rect.w}:${rect.h}`);
    
    console.log(`Success: Coords ${rect.x}:${rect.y}`);
  } catch (err) {
    console.error("FAILED:", err.message);
    process.exit(1);
  } finally {
    if (browser) await browser.close();
  }
})();
