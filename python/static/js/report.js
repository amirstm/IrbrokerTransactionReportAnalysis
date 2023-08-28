function dailyDataChange() {
    filename = window.location.href.split('/').at(-1);
    date = document.getElementById("daily_data").value;
    fetch("/daily_data_report?date="+encodeURIComponent(date)+"&filename="+encodeURIComponent(filename)).then(function(response) {
        return response.text().then(function (text){
            document.getElementById('daily_data_result').innerHTML = text;
        });
      }).then(function(data) {
      }).catch(function(err) {
        console.log('Fetch Error :-S', err);
      });
}