var attempt = 3; // Variable to count number of attempts.
// Below function Executes on click of login button.
function validate(){
var username = document.getElementById("username").value;
var password = document.getElementById("password").value;
if ( username == "userTest" && password == "pass#123"){
alert ("Login cu succes");
window.location = "succes.html"; // Redirecting to other page.
return false;
}
else{
attempt --;// Decrementing by one.
alert("Incercare esuata. Mai aveti "+attempt+"incercari");
// Disabling fields after 3 attempts.
if( attempt == 0){
document.getElementById("username").disabled = true;
document.getElementById("password").disabled = true;
document.getElementById("submit").disabled = true;
return false;
}
}
}