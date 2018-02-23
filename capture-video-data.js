javascript: (function() {
  var GDOC_URL =
    "https://script.google.com/macros/s/AKfycbwSJ8SBv-sWWjsz7uNrx29-7c0GWhk-os0ZsD_bwM_gU_c3TnzQ/exec";
  var player = document.querySelector("#movie_player"),
    time = player.getCurrentTime(),
    url = player.getVideoUrl();

  player.pauseVideo();

  var form = document.createElement("form");
  form.style.setProperty("top", "0px");
  form.style.setProperty("position", "absolute");
  form.style.setProperty("z-index", "10000");
  form.style.setProperty("background", "white");
  form.style.setProperty("padding", "5px");
  form.style.setProperty("width", "310px");

  var call = document.createElement("input");
  call.setAttribute("type", "text");
  call.setAttribute("name", "call");
  call.setAttribute("id", "call");
  call.setAttribute("placeholder", "Enter type of call");
  call.style.setProperty("background-color", "lightpink");
  call.style.setProperty("width", "300px");
  call.style.setProperty("margin", "2px");
  call.style.setProperty("padding", "2px");
  call.style.setProperty("font-family", "monospace");
  form.append(call);

  var comment = document.createElement("textarea");
  comment.setAttribute("placeholder", "Additional comments if any... ");
  comment.style.setProperty("margin", "2px");
  comment.style.setProperty("padding", "2px");
  comment.style.setProperty("width", "300px");
  comment.style.setProperty("height", "200px");
  form.append(comment);

  var submit = document.createElement("button");
  submit.setAttribute("disabled", "1");
  submit.style.setProperty("background-color", "lightgreen");
  submit.textContent = "Submit";
  form.append(submit);
  submit.onclick = function(e) {
    e.preventDefault();
    submit_data(url, time, call.value, comment.value);
    form.remove();
  };
  call.onkeyup = function(e) {
    if (!call.value) {
      submit.setAttribute("disabled", "1");
      call.style.setProperty("background-color", "lightpink");
    } else {
      submit.removeAttribute("disabled");
      call.style.setProperty("background-color", "white");
    }
  };

  var cancel = document.createElement("button");
  cancel.textContent = "X";
  cancel.style.setProperty("border", "0px");
  cancel.style.setProperty("background", "red");
  cancel.style.setProperty("float", "right");
  form.append(cancel);
  cancel.onclick = function() {
    form.remove();
  };

  document.body.append(form);

  var submit_data = function(url, time, call, comment) {
    url = encodeURIComponent(url);
    time = encodeURIComponent(time);
    call = encodeURIComponent(call);
    comment = encodeURIComponent(comment);
    var data_url = `${GDOC_URL}?url=${url}&time=${time}&call=${call}&comment=${comment}`;
    window.open(data_url);
  };
})();
