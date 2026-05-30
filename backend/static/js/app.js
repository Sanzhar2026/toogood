function getLocation() {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(pos => {
            alert("Latitude: " + pos.coords.latitude +
                  " Longitude: " + pos.coords.longitude);
        });
    }
}



function orderFood(id) {
    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(pos => {
            
            fetch("/order", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    food_id: id,
                    lat: pos.coords.latitude,
                    lon: pos.coords.longitude
                })
            })
            .then(res => res.json())
            .then(data => alert("Заказ оформлен!"))
        });
    } else {
        alert("Geolocation not supported");
    }
}