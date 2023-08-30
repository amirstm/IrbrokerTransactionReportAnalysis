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

function chartPlotAll() {
  filename = window.location.href.split('/').at(-1);
  initialInvestment = document.getElementById('initialInvestment').value;
  fetch("/report/" + filename + "/initialInvestment", {
    method: "POST",
    headers: {'Content-Type': 'text/html; charset=utf-8'},
    body: JSON.stringify(initialInvestment)
  }).then(res => {
    console.log("Request complete! response:", res);
  });
  var plotsDiv = document.getElementById("plots_section");
  plotsDiv.innerHTML = "";
  // chart-profit-value
  var img = document.createElement("img");
  img.src = "/report/" + filename + "/chart-profit-value";
  plotsDiv.appendChild(img);
  // chart-profit-percentage
  var img = document.createElement("img");
  img.src = "/report/" + filename + "/chart-profit-percentage";
  plotsDiv.appendChild(img);
  // chart-trade-volume
  var img = document.createElement("img");
  img.src = "/report/" + filename + "/chart-trade-volume";
  plotsDiv.appendChild(img);
}
