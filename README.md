# ECONOMY COMMAND — 5 баг, QR LIVE WEB

## Интернэтээр тоглуулах
1. Энэ хавтсын файлуудыг шинэ GitHub repository-д upload хийнэ.
2. Render Dashboard → New → Blueprint → repository сонгоно (render.yaml автоматаар уншина).
3. Deploy амжилттай болсны дараа Render → Environment → HOST_PIN утгыг харна.
4. Багш: `https://ТАНЫ-САЙТ.onrender.com/?role=host&pin=HOST_PIN`
5. Багшийн дэлгэцэд таван багийн QR гарна. QR тус бүрийг тухайн баг утсаараа уншуулна.
6. Багш PROJECTOR НЭЭХ товч дарна. Тусдаа сүлжээ шаардлагагүй, зөвхөн интернэт.

## Хязгаарлалт
- Free instance унтаад сэрэхэд тоглоом reset болох эрсдэлтэй.
- Сервер дахин эхлэхэд өгөгдөл арилна; чухал тэмцээнд PostgreSQL persistence нэмэх шаардлагатай.
- HOST_PIN-ээ оюутнуудад бүү дамжуул. QR нь тухайн багийн нэвтрэх токен.
- 2004, 2006 оны үйл явдлуудын өгөгдөл нь сургалтын симуляц.


## Байнгын хадгалалт (PostgreSQL)
Render дээр PostgreSQL database үүсгэж, **Internal Database URL**-ийг web service-ийн `DATABASE_URL` environment variable-д холбоно. `HOST_PIN`-ийг тогтмол, нууц утгаар тохируулна. `DATABASE_URL` байхгүй үед локал SQLite ашиглана; Render-ийн ephemeral disk дээр SQLite хадгалалт найдвартай биш.

Хариулт, үе шат, оноо, шийдвэр, тайлбар бүр серверийн database-д хадгалагдана. `ДАХИН ЭХЛЭХ` дарахад өмнөх тоглолт `game_archives` хүснэгтэд хадгалагдана. Багшийн PIN ашиглан `GET /api/archives`, `GET /api/archives/<id>`, `GET /api/export` endpoint-оор архив болон JSON экспорт авч болно. Олон worker ажиллуулахгүй (`--workers 1`).

Анхааруулга: Render Free PostgreSQL-ийн хадгалах хугацаа, нөөцлөлтийн бодлогоос шалтгаалж урт хугацааны хадгалалт баталгаагүй байж болно. Тоглолт бүрийн JSON экспортын нөөц хуулбар авна уу.
