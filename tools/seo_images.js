// Картинки для SEO: img/og.png (превью ссылки 1200×630), img/logo-512.png (логотип для разметки),
// apple-touch-icon.png, favicon.ico. favicon.svg — копия assets/tovar-v-dele-logo-mark.svg.
// Запуск из папки public/: node ../tools/seo_images.js (нужен Playwright с Chromium).
const {chromium}=require('playwright');const fs=require('fs');
const mark=fs.readFileSync('favicon.svg','utf8');
(async()=>{const b=await chromium.launch();
const shot=async(w,h,body,out)=>{const p=await b.newPage({viewport:{width:w,height:h}});
await p.setContent(`<!doctype html><html><head><link href="https://fonts.googleapis.com/css2?family=Onest:wght@400;500;900&display=swap" rel="stylesheet"><style>html,body{margin:0;width:${w}px;height:${h}px;overflow:hidden}body{font-family:Onest,sans-serif}</style></head><body>${body}</body></html>`,{waitUntil:'networkidle'});
await p.evaluate(()=>document.fonts.ready);await p.screenshot({path:out,omitBackground:true});await p.close();};
const icon=(sz,pad,bg)=>`<div style="width:${sz}px;height:${sz}px;display:grid;place-items:center;background:${bg}">${mark.replace('<svg ',`<svg style="width:${sz-2*pad}px;height:${sz-2*pad}px" `)}</div>`;
await shot(512,512,icon(512,56,'#fff'),'img/logo-512.png');
await shot(180,180,icon(180,22,'#fff'),'apple-touch-icon.png');
await shot(32,32,icon(32,1,'transparent'),'favicon.ico.png');
// favicon.ico: ICO-контейнер с одной PNG 32×32 внутри
const png=fs.readFileSync('favicon.ico.png');fs.unlinkSync('favicon.ico.png');
const h=Buffer.alloc(22);h.writeUInt16LE(0,0);h.writeUInt16LE(1,2);h.writeUInt16LE(1,4);
h.writeUInt8(32,6);h.writeUInt8(32,7);h.writeUInt16LE(1,10);h.writeUInt16LE(32,12);h.writeUInt32LE(png.length,14);h.writeUInt32LE(22,18);
fs.writeFileSync('favicon.ico',Buffer.concat([h,png]));
await shot(1200,630,`<div style="position:relative;width:1200px;height:630px;background:#F4F8FE;color:#0A1736;box-sizing:border-box;padding:64px 72px">
<div style="display:flex;align-items:center;gap:16px">${mark.replace('<svg ','<svg style="width:66px;height:61px" ')}<span style="font-weight:900;font-size:33px;line-height:.88;letter-spacing:-.035em;color:#072446">Товар<br>в деле</span></div>
<div style="position:absolute;left:72px;right:72px;bottom:64px">
<div style="font-size:38px;line-height:1.25;color:#1246D6;letter-spacing:-.01em;margin-bottom:14px">Фулфилмент для маркетплейсов<br>и интернет-магазинов</div>
<div style="font-size:188px;line-height:.92;font-weight:500;letter-spacing:-.055em;color:#1A5CFF;margin-left:-8px;white-space:nowrap">Товар в деле</div>
<div style="margin-top:34px;font-size:26px;color:#0A1736;opacity:.72">Склад в Туле · FBS · FBO · Хранение · Wildberries, Ozon, Яндекс Маркет</div></div></div>`,'img/og.png');
await b.close();})();
