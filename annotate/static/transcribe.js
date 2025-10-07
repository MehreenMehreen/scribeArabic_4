// There are three types of lines: Empty unfilled textboxes, Filled textboxes and selected textboxes in focus

let LEFT_PAGE = 0;
let RIGHT_PAGE = 0;
let JSON_OBJ = null;

EMPTY_STROKE_COLOR = "rgba(0, 0, 0, 0.5)";
EMPTY_FILL_COLOR = "rgba(220, 220, 220, 0.3)";
TEXTBOX_BACKGROUND = "rgba(255, 255, 255, 0)"; //# Transparent
SELECTED_LINE_STROKE = "rgba(0, 0, 0, 0)";
SELECTED_LINE_FILL = "rgba(255, 255, 255, 0.9)";

// Fields for when data is filled

DATA_LINE_STROKE = "rgba(0, 0, 0, 0.2)";
DATA_LINE_FILL = "rgba(200, 200, 200, 0.9)";

FILLED_TEXTBOX_BACKGROUND = "rgba(200, 200, 200, 0.99)";

class transcribePage extends manuscriptPage {
  constructor(imageWidth, canvasId="imgCanvas", imageId="manuscript") {
    super(imageWidth, canvasId, imageId);
  	this.textBoxArray = 0;  
  }
  initializeLines(linesJson) {
  	super.initializeLines(linesJson);
  	
  	var minX=0, maxX=0, minY=0, maxY=0;
		let canvasRect = this.canvas.getBoundingClientRect();

  	this.textBoxArray = new Array(this.lineArray.length);
  	for (var i=0;i<this.textBoxArray.length;++i) {
  		[minX, minY, maxX, maxY] = this.lineArray[i].getCornerPts();
      var [angle, start_y] = this.lineArray[i].getLineAngle_y();
  		var input = document.createElement('input');
			input.type = 'text'; 
			input.style.width = (maxX-minX) + 'px'; // Adjust the width as needed
			input.style.padding = '5px'; // Adjust the padding as needed
			input.placeholder = 'أدخل نصآ';
			//input.placeholder = 'Line ' + i;
  		input.style.backgroundColor = TEXTBOX_BACKGROUND;
  		input.style.border = "transparent"
  		input.style.color = "black"
  		input.style.fontWeight = "bolder"
	
			input.style.position = 'absolute';
			input.style.left = canvasRect.left + minX + 'px';
			input.style.top = canvasRect.top + window.scrollY + start_y - 25 + 'px';
			input.style.height = '50px';
			input.setAttribute('lang', 'ar');
			input.setAttribute('dir', 'rtl');

      input.style.transform = "rotate("+angle+"deg)";
      input.style.transformOrigin = 100 + "% " + 100 + "%";
			// Append the main container div to the document body
			document.body.appendChild(input);

			this.textBoxArray[i] = input;
			input.addEventListener('keyup', keyUpEvent);
			//input.addEventListener('click', function() {
			//do nothing
			//	alert('click');
			//});
  	}
    this.loadTextBoxes();  
  	this.selectedIndex = 0;
  	this.refreshLines();
  }

  loadTextBoxes() {
      for (var i=0;i < this.textBoxArray.length;++i)
          this.textBoxArray[i].value = this.lineArray[i].text;
  }
    
    
  changeSelectedIndex() {
  	let index = this.selectedIndex;
  	if (index == -1 || this.lineArray.length == 0)
  		return;

  	let ctx = this.canvas.getContext("2d");
  	ctx.save();
  	ctx.strokeStyle = SELECTED_LINE_STROKE;
    ctx.fillStyle = SELECTED_LINE_FILL;
    this.lineArray[index].stroke(ctx);
    this.lineArray[index].fill(ctx);

    this.textBoxArray[index].focus();

  	ctx.restore();
  }

  //Todo: Delete this method. Not needed
  refreshTextBoxes() {
  	for (var i=0;i<this.textBoxArray.length;++i) {
      var [angle, start_y] = this.lineArray[i].getLineAngle_y();
  		input = textBoxArray[i];
  		input.style.backgroundColor = TEXTBOX_BACKGROUND;
  		input.style.border = "transparent";
  		input.style.color = "black";
  		input.style.fontWeight = "bolder";
      input.style.transform = "rotate("+angle+"deg)";
      input.style.transformOrigin = 100 + "% " + 100 + "%";
  	}
  }    
      
  getJsonString(submit=false, checked=false) {
    this.submit = submit;
    this.checked = checked;
    // set the value in textArray
    for (let i=0; i<this.textBoxArray.length; ++i) {
      this.lineArray[i].text = this.textBoxArray[i].value;
    }
    // Get the JSON with coordinates from parent object 
    let linesJsonString = super.getJsonString(submit);
    
        
    return linesJsonString;
  }  
  

  refreshLines() {
  	this.refreshManuscript();
  	let ctx = this.canvas.getContext("2d");

  	ctx.save();
    
    ctx.strokeStyle = EMPTY_STROKE_COLOR;
    ctx.fillStyle = EMPTY_FILL_COLOR;
    
    for (let i=0;i<this.lineArray.length;++i) {
    	this.textBoxArray[i].blur();
    	if (this.textBoxArray[i].value.length == 0) {
	    	this.lineArray[i].stroke(ctx);
  	    this.lineArray[i].fill(ctx);
  	  }
    }   
    ctx.strokeStyle = DATA_LINE_STROKE;
    ctx.fillStyle = DATA_LINE_FILL;
    for (let i=0;i<this.lineArray.length;++i) {
    	if (this.textBoxArray[i].value.length > 0) {
	    	this.lineArray[i].stroke(ctx);
  	    this.lineArray[i].fill(ctx);
  	  }
    }   

    ctx.restore();
    this.changeSelectedIndex();
  }

  inputEndKeyPressed() {
  	
  	this.selectedIndex = (this.selectedIndex + 1) % this.lineArray.length;
  	this.refreshLines();
  	console.log(this.selectedIndex);
  	
  }
  MouseClick(mouseX, mouseY) {
  	//alert(mouseX);
  	let ctx = this.canvas.getContext("2d");
  	let index = this.getSelectedLineIndex(ctx, mouseX, mouseY);
    if (index == -1 ) 
    	return;
    
    this.selectedIndex = index;
    this.refreshLines();

  }
}


function appendImg(img_src, id) {
	img_node = document.createElement("IMG");
	img_node.id = id;
	img_node.src = img_src;
	img_node.hidden = true;
	document.body.appendChild(img_node);
}

function fill_select_json_files(json_obj) {
	leftSelect = document.getElementById("leftSelect")
	// Left side selection
	for (let i=0;i<json_obj.fileList.length;++i) {
      let opt = document.createElement("option");
      opt.innerHTML = json_obj.fileList[i];
      leftSelect.appendChild(opt);      
  }
  leftSelect.selectedIndex = 0;
}



function initPage(leftImg, rightImg, jsonObj){

  // Make the relevant button visible
  if (!CHECKING) {
    var button = document.getElementById("checkTranscript");
    button.style.display = "none";
  }
  else {
    var button = document.getElementById("submitTranscript");
    button.style.display = "none";
  }
  


	JSON_OBJ = jsonObj;
	// Set the image labels
	document.getElementById("leftImageName").innerHTML = leftImg;
	document.getElementById("rightImageName").innerHTML = rightImg;
	// Create the image nodes in document
	leftCanvas = document.getElementById("leftCanvas");
	rightCanvas = document.getElementById("rightCanvas");
	appendImg(leftImg, "leftSideImage");
	appendImg(rightImg, "rightSideImage");
	

	
	//Creat the left and right page
	LEFT_PAGE = new transcribePage(leftCanvas.getBoundingClientRect().width, "leftCanvas", "leftSideImage");
	RIGHT_PAGE = new manuscriptPage(rightCanvas.getBoundingClientRect().width, "rightCanvas", "rightSideImage");

	//Set the select options
	fill_select_json_files(jsonObj);
    leftSelectJson();

  document.addEventListener("mousedown", onMouseClickLeft);
  LEFT_PAGE.changeSelectedIndex(0);
  RIGHT_PAGE.changeSelectedIndexForView(0);

}

function onMouseClickLeft(event) {

	//alert('mouse in parent');
	const canvasBounds = leftCanvas.getBoundingClientRect();
  const mouseX = event.clientX - canvasBounds.left;
  const mouseY = event.clientY - canvasBounds.top;
	LEFT_PAGE.MouseClick(mouseX, mouseY);
	index = LEFT_PAGE.getSelectedIndex();
	RIGHT_PAGE.changeSelectedIndexForView(index);


}



function keyUpEvent(event) {

	if (event.key == 'Enter' || (event.key == 'Escape') || (event.key == 'Tab'))	{
		LEFT_PAGE.inputEndKeyPressed();
		event.stopPropagation();

		index = LEFT_PAGE.getSelectedIndex();
		RIGHT_PAGE.changeSelectedIndexForView(index);

		//alert('key', event.key)
	}
}

function onMouseMoveLeftView(event) {
  

}
 
function onMouseMoveRightView(event) {


}

function postViewForm(flag) {
  if (flag < 1 || flag > 6)
        return;
    let submit = false;
    let checked = false;
	//Previous pressed
	if (flag == 1) {
		document.getElementById('transcribeInput').name='previous';
	}
	//next pressed
	else if (flag == 2) {
		document.getElementById('transcribeInput').name='next';
	}
    //save pressed
  else if (flag == 3) {
    document.getElementById('transcribeInput').name='save';
  }
  //end pressed
  else if (flag ==4) {
        document.getElementById('transcribeInput').name='end';
  }
  else if (flag == 5) {
    if (!confirm("Are you sure you want to submit this transcription?"))
        return;
    	// Submit clicked
    	document.getElementById('transcribeInput').name='submit';
      submit = true;
      checked = false;
  }
  else if (flag == 6) {
    if (!confirm("Save this transcription as checked?"))
        return;
    	// checked clicked
    document.getElementById('transcribeInput').name='checked';
    checked = true;
    submit = false;

  }
    let scrollPosition = getScrollPosition();
    let image_name = document.getElementById("rightImageName").innerHTML
    let jsonToPost = {"images_obj": IMAGES, "admin": ADMIN, 
                      "page_json": LEFT_PAGE.getJsonString(submit, checked),
                     "scroll_position": {"x": scrollPosition.x, "y": scrollPosition.y}};

    document.getElementById('transcribeInput').value= JSON.stringify(jsonToPost);
    document.getElementById('transcribeForm').submit();

}

function leftSelectJson() {
    let selectedFile = document.getElementById("leftSelect");
    let ind = selectedFile.selectedIndex;
    filename = selectedFile.options[ind].innerHTML;
    LEFT_PAGE.refreshManuscript();
  
    LEFT_PAGE.initializeLines(JSON_OBJ[filename]);    
    RIGHT_PAGE.initializeLines(JSON_OBJ[filename]);

}

function getScrollPosition() {
  var scrollPosition = {
    x: window.pageXOffset || document.documentElement.scrollLeft,
    y: window.pageYOffset || document.documentElement.scrollTop
  };
  return scrollPosition;
}

