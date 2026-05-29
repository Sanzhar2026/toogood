# // Проверяем API с вашими координатами
# const userLat = 50.28922594440174;
# const userLon = 57.14937759403024;

# fetch(`https://toogood-2ncf.onrender.com/api/suppliers/nearby?lat=${userLat}&lon=${userLon}&radius=100`)
#   .then(r => r.json())
#   .then(data => {
#     console.log('📦 API вернул магазины:', data.suppliers?.map(s => s.business_name));
#     console.log('Количество:', data.suppliers?.length);
#   });

# // Проверяем, есть ли этот магазин в общем списке
# fetch('https://toogood-2ncf.onrender.com/api/suppliers')
#   .then(r => r.json())
#   .then(data => {
#     const we = data.find(s => s.business_name === 'we');
#     console.log('Магазин "we" в БД:', we);
#     console.log('Его координаты:', we?.lat, we?.lon);
#     console.log('Активен:', we?.is_active);
#   });