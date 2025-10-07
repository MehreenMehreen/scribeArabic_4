// There are three types of lines: Empty unfilled textboxes, Filled textboxes and selected textboxes in focus

let LEFT_PAGE = 0;
let RIGHT_PAGE = 0;
let JSON_OBJ = null;
const lineAddedEvent = new Event("lineAdded");
let MOUSE_X = 0;
let MOUSE_Y = 0;
let MOUSE_IN_RIGHT_CANVAS = false;
let LINE_BY_LINE = true;
let ZOOM_FACTOR = 1.0;

let EMPTY_STROKE_COLOR = "rgba(0, 0, 0, 0.5)";
let EMPTY_FILL_COLOR = "rgba(220, 220, 220, 0.3)";
let TEXTBOX_BACKGROUND = "rgba(255, 255, 255, 0.8)"; //# Transparent
let SELECTED_LINE_STROKE = "rgba(0, 0, 0, 0)";
let SELECTED_LINE_FILL = "rgba(255, 255, 255, 0.9)";


// Fields for when data is filled

let DATA_LINE_STROKE = "rgba(0, 0, 0, 0.2)";
let DATA_LINE_FILL = "rgba(200, 200, 200, 0.9)";

let SELECTED_TEXTBOX_BACKGROUND = "rgba(255, 255, 255, 1)";
let TAG_CHECKBOX_ID = "tagCheckBox";
// For tagging
let REGION_FILL_COLOR = "rgba(20, 20, 250, 0.1)";
let TAGGED_STROKE_COLOR = "rgba(0, 0, 255, 0.5)";
let BUTTON_TEXT_NO_TAG = "<i class='fa'>&#xf150</i>"
let BUTTON_TEXT_TAG = "<i class='fa'>&#xf191</i>"
let SELECTED_BUTTON_BK_COLOR = "rgba(0, 0, 128, 0.5)";
let NORMAL_BUTTON_BK_COLOR = "rgba(211, 211, 211, 0.5)";
let TAG_DIV_CONTAINER = "TAG_DIV_CONTAINER-";
let TEXTBOX_HT = "50px"

//This class handles all the markings
class annotateBlock extends manuscriptPage {
	constructor(imageWidth, canvasId="imgCanvas", imageId="manuscript") {
    super(imageWidth, canvasId, imageId);
    //has index of line being changed
    this.lineChanging = -1;
    this.zoomOn = false;
    this.zoomFactor = ZOOM_FACTOR;
  	
  }
  setNormalMode() {

  	super.setNormalMode();
  	
  	if (this.lineChanging != -1) {


  	//	var data = {'lineIndex': this.lineChanging};
  	//	var lineChangedEvent = new CustomEvent('lineChangedEvent', {detail: data});
  	//	document.dispatchEvent(lineChangedEvent);


  		var scrollPosition = getScrollPosition();
			
			var line = this.getLine(this.lineChanging);
			LEFT_PAGE.changeLine(this.lineChanging, line);
			window.scrollTo(scrollPosition.x, scrollPosition.y);
		}
  	this.lineChanging = -1;
  }

  restoreNormal(index) {

  	this.setNormalMode();
  	this.mouseDrag = false;
  	this.drawLine = null;
  	const ctx = this.canvas.getContext("2d");
    ctx.save();
    //this.refreshLines();
    this.refreshManuscript();
    this.selectedIndex = index;
    this.showSelected(MOVE_STYLE);
    ctx.restore();
    this.lineChanging = -1;
  }

  pencilDoubleClick(event) {
  	let totalLines = this.lineArray.length;
  	super.pencilDoubleClick(event);
  	// Was line added
  	let lastIndex = this.lineArray.length - 1;
  	//Check if line was added
  	if (lastIndex == totalLines) {
  		document.dispatchEvent(lineAddedEvent);
  	}
  }

  pasteClicked() {
		let totalLines = this.lineArray.length;
		super.pasteClicked();
		// Was line added
  	let lastIndex = this.lineArray.length - 1;
  	//Check if line was added
  	if (lastIndex == totalLines) {
  		document.dispatchEvent(lineAddedEvent);
  	}
	}

	getLastLine() {
		return this.lineArray[this.lineArray.length - 1];
	}

	setModified() {
		// to not have to set undo and other buttons
    this.modified = true;
  }
  setMoveMode() {
  	this.lineChanging = this.selectedIndex;
  	super.setMoveMode();
  }

  getLine(index) {
  	if (index < 0 || index >= this.lineArray.length)
  		return null;
  	return this.lineArray[index];
  }
  deleteLine() {
  	let index = this.selectedIndex;
    if (index < 0 || index >= this.lineArray.length)
        return -1
  	super.deleteClicked();
  	return index;
  }
  //from textine class
  coordToPixel(coord, displayedImageWidth) {

		var ratio = this.imageDim.x/displayedImageWidth;
  	var imageDim = this.imageDim;

  	var p = new myPoint();
  	
  	p.x = coord.x * ratio;
  	p.y = coord.y * ratio;

  	return p;
  }

  onMouseMove(event){
  	super.onMouseMove(event);
  	if (this.zoomOn)
	  	this.fillZoomBox();
  }

  zoomPlus() {
  	this.zoomOn = true;
  	this.zoomFactor += 0.1;
  	const modal = document.getElementById('myModal');
  	modal.style.top = '80%';
    modal.style.left = '5%';
    modal.style.width = '90%';
    modal.style.height = '20%'
    modal.style.position = 'fixed';
  	modal.style.display = 'flex';

  	this.fillZoomBox();
  	ZOOM_FACTOR = this.zoomFactor;

  }

  zoomMinus() {
  	this.zoomOn = true;
  	this.zoomFactor -= 0.1;
  	const modal = document.getElementById('myModal');
  	modal.style.top = '80%';
    modal.style.left = '5%';
    modal.style.width = '90%';
    modal.style.height = '20%'
    modal.style.position = 'fixed';
  	modal.style.display = 'flex';

  	this.fillZoomBox();
  	ZOOM_FACTOR = this.zoomFactor;
  }

  zoomClose() {
  	this.zoomOn = false;
  }

  fillZoomBox(mousePosition = null) {
  	if (!this.zoomOn)
  		return;
  	//var logBox = document.getElementById('log5');
  	var factor = this.zoomFactor;
  	const modal = document.getElementById('myModal');
  	const zoomBox = document.getElementById('zoomBox');
  	var modalBox = modal.getBoundingClientRect();
  	var ratioZoomBox = modalBox.width/this.imageDim.x*factor;

  	if (mousePosition == null) {
	  	mousePosition = new myPoint(this.mousePosition.x, this.mousePosition.y);

  	}

  	
  	
  	// Location of mouse cursor in pixels
  	var mouseLocPixels = this.coordToPixel(mousePosition, this.displayedImageDim.x);
  	
  	if (mouseLocPixels.x < 0) mouseLocPixels.x = 0;
  	if (mouseLocPixels.y < 0) mouseLocPixels.y = 0;
  	//convert the pixels to zoom box coordinates
  	var pos = new myPoint(ratioZoomBox*mouseLocPixels.x, ratioZoomBox*mouseLocPixels.y)
  	var maxXPos = modalBox.width*factor - modalBox.width ;
  	
  	
  	//Add offset to center of modal box
  	pos.x = pos.x - modalBox.width/2;
  	pos.y = pos.y - modalBox.height/2;
  	if (pos.x < 0) pos.x = 0;
  	if (pos.y < 0) pos.y = 0;
  	if (factor <= 1) pos.x = 0;
  	if (factor > 1 && pos.x>maxXPos) pos.x = maxXPos;
  	

  	zoomBox.style.backgroundSize = (factor*100) + '%';
  	zoomBox.style.backgroundPosition = -pos.x + 'px ' + (-pos.y) + 'px';
  	zoomBox.style.backgroundRepeat = "no-repeat"; 
  	
  }

  reinitialize(linesJson, widthImg) {
  	super.displayManuscript(widthImg)
  	this.refreshManuscript();	
  	super.reinitializeLines(linesJson);
  	super.refreshLines();
  }

}

//This class handles all the textboxes
class transcribeBlock extends manuscriptPage {
  constructor(imageWidth, canvasId="imgCanvas", imageId="manuscript") {
    super(imageWidth, canvasId, imageId);
  	this.textBoxArray = 0;  
  	// This holds a map of all textboxes that link them to an index
  	// The index is the associated lineArray
  	this.textBoxMap = new Map();
  	this.userType = "transcription_tagging";
    	if (CHECKING) this.userType = "transcription_tagging_QA";  
    this.lineRotated = false;
  	
  }

  //Any change here should also be made in changeLine (called after annotation modification)
  getInputObject(minX, minY, maxX, maxY, canvasRect, angle=0, start_y=0, 
  	             vertical=false) {
  	
  	let ht="50px";
    if (TEXTBOX_HT == 0) {
        ht = (maxY-minY) + 'px';
        angle = 0;
    }
  	var input = document.createElement('textarea');
		input.rows = 1;
		input.cols = 200;

		
		input.style.width = Math.max((maxY-minY), (maxX-minX)) + 'px'; // Adjust the width as needed
		input.style.padding = '5px'; // Adjust the padding as needed
		input.placeholder = 'أدخل نصآ';
 
		input.style.backgroundColor = TEXTBOX_BACKGROUND;
		input.style.border = "transparent";
		input.style.color = "black";
		input.style.fontWeight = "bolder";

		input.style.position = 'absolute';
		input.style.left = canvasRect.left + window.scrollX + minX + 'px';
		input.style.top = canvasRect.top + window.scrollY + start_y - 25 + 'px';
        if (TEXTBOX_HT == 0) input.style.top = canvasRect.top + window.scrollY + minY + 'px'
		input.style.height = ht; 
		input.setAttribute('lang', 'ar');
		input.setAttribute('dir', 'rtl');
        let relative_y = 100;
        let relative_x = 100;
        if ((maxX-minX) < (maxY-minY)) {
            relative_x=100;relative_y = 0;
            let avgX = parseInt((maxX + minX)/2)
            // Place the textbox so that right corner is at maxX...so need to adjust left according to
            //width of box which is maxY-minY
            if (Math.abs(angle) < 90) {
            input.style.left = canvasRect.left + window.scrollX + (maxX-(maxY-minY)) + 'px';}
            else {
                input.style.left = canvasRect.left + window.scrollX + (minX-(maxY-minY)) + 'px';}
            input.style.top = canvasRect.top + window.scrollY + minY + 'px';
            //angle = 0;
        }
		input.style.transform = "rotate("+angle+"deg)";
		input.style.transformOrigin = relative_x + "% " + relative_y + "%";
		if (vertical){
			//angle = -90 or 90;
			input.style.width = (maxY-minY) + 'px';
			input.style.top = canvasRect.top + window.scrollY + minY + 'px';
			input.style.left = canvasRect.left + window.scrollX + minX + 'px';
			input.style.height = ht; 
			input.style.transformOrigin = "0% 0%";
			input.style.transform = "rotate("+angle+"deg)";
			//bottom to top
			input.style.top = canvasRect.top + window.scrollY + minY + 'px';
			input.style.left = canvasRect.left + window.scrollX + maxX + 'px';
			if (angle < 0) { //top to bottom
				input.style.top = canvasRect.top + window.scrollY + maxY + 'px';
				input.style.left = canvasRect.left + window.scrollX + minX + 'px';
			}
		}

		return input;

  }
  initializeLines(linesJson) {
  	super.initializeLines(linesJson);
  	let vertical = false;
  	
  	var minX=0, maxX=0, minY=0, maxY=0;
		let canvasRect = this.canvas.getBoundingClientRect();

  	this.textBoxArray = new Array(this.lineArray.length);
  	for (var i=0;i<this.textBoxArray.length;++i) {
  		vertical = false;
  		[minX, minY, maxX, maxY] = this.lineArray[i].getCornerPts();
  		var [angle, start_y] = this.lineArray[i].getLineAngle_y();
  		if (this.lineArray[i].isVerticalOrientation()) {
  			vertical = true;
  			if (this.lineArray[i].isVerticalTopDown()){
  				angle = -90;
  			}
  			else {
  				angle = 90
  			}
  		}
        this.lineArray[i].angle = angle;
  		let input = this.getInputObject(minX, minY, maxX, maxY, canvasRect, angle, 
  																		start_y=start_y, vertical=vertical);
			// Append the main container div to the document body
			document.body.appendChild(input);
			this.textBoxArray[i] = input;
			input.addEventListener('keyup', keyUpEvent);
			input.addEventListener('focus', onTextAreaFocus);
			input.addEventListener('blur', onTextAreaBlur);
			this.textBoxMap.set(input, i);
			
			
  	}
    this.loadTextBoxes();  
  //	this.selectedIndex = 0;
  	this.refreshLines();

  	
  }

  reinitialize(linesJson, widthImg) {
  	super.displayManuscript(widthImg);
  	this.refreshManuscript(); 	
  	var minX=0, maxX=0, minY=0, maxY=0;
		let canvasRect = this.canvas.getBoundingClientRect();
  	super.reinitializeLines(linesJson);
  	super.refreshLines();
  	let vertical = false;

  	//this.textBoxArray = new Array(this.lineArray.length);
  	for (var i=0;i<this.textBoxArray.length;++i) {
  		vertical = false;
  		[minX, minY, maxX, maxY] = this.lineArray[i].getCornerPts();
  		var [angle, start_y] = this.lineArray[i].getLineAngle_y();

  		if (this.lineArray[i].isVerticalOrientation()) {
  			vertical = true;
  			if (this.lineArray[i].isVerticalTopDown()){
  				angle = -90;
  			}
  			else {
  				angle = 90
  			}
  		}
        this.lineArray[i].angle = angle

  		let input = this.getInputObject(minX, minY, maxX, maxY, canvasRect, angle, start_y, vertical);
			// Append the main container div to the document body

			document.body.appendChild(input);
			//save text in old textbox
			var text = this.textBoxArray[i].value;
			//Remove the current textbox
			
			this.textBoxArray[i].value = "";
			this.textBoxArray[i].remove();
			//update the textbox
			this.textBoxArray[i] = input;
			this.textBoxArray[i].value = text;
			
			input.addEventListener('keyup', keyUpEvent);
			input.addEventListener('focus', onTextAreaFocus);
			input.addEventListener('blur', onTextAreaBlur);
			this.textBoxMap.set(input, i);
  	} 
    let taggedStyle = "";;
    if (this.showRegions) taggedStyle = "visible"; else taggedStyle = "hidden"  ;
    for (var i=0;i<this.lineArray.length;++i)
    {
        if (this.lineArray[i].isRegion()) {
            this.textBoxArray[i].style.visibility = taggedStyle;
        }
    }
  }

  loadTextBoxes() {
      for (var i=0;i < this.textBoxArray.length;++i)
          this.textBoxArray[i].value = this.lineArray[i].text;
  }
    
    
  changeSelectedIndex() {
  	let index = this.selectedIndex;
  	if (index == -1)
  		return;
  	if (this.lineArray.length == 0)
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

  
      
  getJsonString(submit=false, checked=false) {
    this.submit = submit;
    this.checked = checked;
    // set the value in textArray
    for (let i=0; i<this.textBoxArray.length; ++i) {
      this.lineArray[i].text = this.textBoxArray[i].value;
    
    // TODO: get a better way of doing this
    // Copy all tags from right page to left page
    // Get the JSON with coordinates from parent object 
      this.lineArray[i].copyTags(RIGHT_PAGE.lineArray[i].tagDict);
    }
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
      
    let taggedStyle = "";;
    if (this.showRegions) taggedStyle = "visible"; else taggedStyle = "hidden"  ;
    for (var i=0;i<this.lineArray.length;++i)
    {
        if (this.lineArray[i].isRegion()) {
            this.textBoxArray[i].style.visibility = taggedStyle;
        }
    }  

    ctx.restore();
    this.changeSelectedIndex();
  }

  inputEndKeyPressed() {
  	if (this.selectedIndex < 0 || this.selectedIndex >= this.lineArray.length)
  		return;
  	//only one line allowed
  	if (LINE_BY_LINE) {
  		let text = this.textBoxArray[this.selectedIndex].value;
  		if (text.length > 0 && text[text.length-1] == '\n')
  			text = text.replace('\n', "");
  			this.textBoxArray[this.selectedIndex].value = text.slice();
  	}
    // Find an untagged line to display
    for (let i=0; i<this.lineArray.length;++i) {  
        this.selectedIndex = (this.selectedIndex + 1) % this.lineArray.length;
        if (this.showRegions || !this.lineArray[this.selectedIndex].isRegion())
            break
    }
  	this.refreshLines();
  	console.log(this.selectedIndex);
  	
  }
  MouseClick(mouseX, mouseY) {
  	
  	let ctx = this.canvas.getContext("2d");
  	let index = this.getSelectedLineIndex(ctx, mouseX, mouseY);
//    if (index == -1 ) 
//    	return;
    
    this.selectedIndex = index;
    this.refreshLines();

  }
  addLine(line) {

  	let canvasRect = this.canvas.getBoundingClientRect();
  	let newLine = line.createCopy(true);
  	
		let [minX, minY, maxX, maxY] = line.getCornerPts();
		let [angle, start_y] = line.getLineAngle_y();
		let vertical = false;
		if (line.isVerticalOrientation()) {
  			vertical = true;
  			if (line.isVerticalTopDown()){
  				angle = -90;
  			}
  			else {
  				angle = 90
  			}
  		}

    newLine.angle = angle;
  	let input = this.getInputObject(minX, minY, maxX, maxY, canvasRect, angle, start_y, vertical);
		// Append the main container div to the document body
		 document.body.appendChild(input);
		this.textBoxArray.push(input);
		input.addEventListener('keyup', keyUpEvent);
		input.addEventListener('focus', onTextAreaFocus);
		input.addEventListener('blur', onTextAreaBlur);
		this.textBoxMap.set(input, this.lineArray.length);

		this.lineArray.push(newLine);
		this.refreshLines();
  }

  changeLine(index, line) {
  	
    let ht="50px";
  	let vertical = false;
  	//If index out of range
  	if (index < 0 || index >= this.lineArray.length || line==null)
  		return;
  	let canvasRect = this.canvas.getBoundingClientRect();
  	let newLine = line.createCopy(true);
  	
  	this.lineArray[index] = newLine;

	let [minX, minY, maxX, maxY] = line.getCornerPts();
	var [angle, start_y] = line.getLineAngle_y();
    this.textBoxArray[index].style.width = Math.max((maxY-minY), (maxX-minX)) + 'px';
		
  	this.textBoxArray[index].style.left = canvasRect.left + window.scrollX + minX + 'px';
	this.textBoxArray[index].style.top = canvasRect.top + window.scrollY + start_y - 25 + 'px';
    if (TEXTBOX_HT == 0) {
        this.textBoxArray[index].style.top = canvasRect.top + window.scrollY + minY + 'px';
        angle = 0;
        ht = maxY - minY;
    }
    this.textBoxArray[index].style.height = ht;//(maxY-minY) + 'px';

    let relative_y = 100;
    let relative_x = 100;
    if ((maxX-minX) < (maxY-minY)) {
        relative_x=100;relative_y = 0;
        let avgX = parseInt((maxX + minX)/2)
        // Place the textbox so that right corner is at maxX...so need to adjust left according to
        //width of box which is maxY-minY
        if (Math.abs(angle) < 90) {
            this.textBoxArray[index].style.left = canvasRect.left + window.scrollX + (maxX-(maxY-minY)) + 'px';}
            else {
                this.textBoxArray[index].style.left = canvasRect.left + window.scrollX + (minX-(maxY-minY)) + 'px';}

        this.textBoxArray[index].style.top = canvasRect.top + window.scrollY + minY + 'px';
        //angle = 0;
    }
    this.textBoxArray[index].style.transform = "rotate("+angle+"deg)";
    this.textBoxArray[index].style.transformOrigin = relative_x + "% " + relative_y + "%";
      
      
        
		

		//check if vertical
		if (this.lineArray[index].isVerticalOrientation()) {
			vertical = true;
			if (this.lineArray[index].isVerticalTopDown()){
				angle = -90;
			}
			else {
				angle = 90
			}
            this.lineArray[index].angle = angle;
			let input = this.textBoxArray[index];
            input.style.width = (maxY-minY) + 'px';
			input.style.height = "50px";
			input.style.top = canvasRect.top + window.scrollY + minY + 'px';
			input.style.left = canvasRect.left + window.scrollX + maxX + 'px';
			input.style.transformOrigin = "0% 0%";
			input.style.transform = "rotate("+angle+"deg)";
			//bottom to top
			input.style.top = canvasRect.top + window.scrollY + minY + 'px';
			input.style.left = canvasRect.left + window.scrollX + maxX + 'px';
			if (angle < 0) { //top to bottom
				input.style.top = canvasRect.top + window.scrollY + maxY + 'px';
				input.style.left = canvasRect.left + window.scrollX + minX + 'px';
			}


  		}


		this.selectedIndex = -1;
		this.refreshLines();  
	}

	deleteLine(index) {
		if (index < 0 || index >= this.lineArray.length)
  		return;
  	this.lineArray.splice(index, 1);
  	document.body.removeChild(this.textBoxArray[index]);
		this.textBoxArray.splice(index, 1);

		//update the textBoxMap
		for (var i=index;i<this.textBoxArray.length;++i)
			this.textBoxMap.set(this.textBoxArray[i], i);

		this.selectedIndex = -1;
		this.refreshLines();

	}
	onTextAreaFocus(event) {
        this.lineRotated = false;
		let textElement = event.target;
		if (!this.textBoxMap.has(textElement))
			return;

		for (var i=0;i<this.textBoxArray.length;++i) {
			this.textBoxArray[i].style.visibility = "hidden";
		}

		textElement.classList.toggle("form-control");
		textElement.style.color = "black";
		textElement.style.visibility = "visible";
		textElement.style.backgroundColor = SELECTED_TEXTBOX_BACKGROUND;
        
        
        
        
		let index = this.textBoxMap.get(textElement);
        
        if (this.lineArray[index].isNearVertical) {
            textElement.style.transformOrigin = "0% 0%";
			textElement.style.transform = "rotate("+0+"deg)";
            this.lineRotated = true;
        }
        
		if (index < this.lineArray.length && index >= 0) {
			this.lineArray[index].transcribeTimeStart = new Date();
		}



	}

	onTextAreaBlur(event) {
		let textElement = event.target;
		if (!this.textBoxMap.has(textElement))
			return;
		textElement.classList.toggle("form-control");
		textElement.style.backgroundColor = TEXTBOX_BACKGROUND;
		for (var i=0;i<this.textBoxArray.length;++i) {
			this.textBoxArray[i].style.visibility = "visible";
		}
		let index = this.textBoxMap.get(textElement);
        
        if (this.lineArray[index].isNearVertical) {
            textElement.style.transformOrigin = "100% 0%";
			textElement.style.transform = "rotate("+this.lineArray[index].angle+"deg)";
            this.lineRotated = false
        }
        
		if (index < this.lineArray.length && index >= 0) {
			this.lineArray[index].transcribeTime += Math.round((new Date() - 
				                                     this.lineArray[index].transcribeTimeStart)/1000);
		}
	}

	convertNumberToArabic(text) {

		var id = ['٠', '١', '٢', '٣', '٤', '٥', '٦', '٧', '٨', '٩'];
 			return text.replace(/[0-9]/g, function(w){
  			return id[+w]
 			});
	}

	convertNumbers() {

		// IF a line is selected change only that line
		if (this.selectedIndex >= 0 && this.selectedIndex < this.textBoxArray.length) {
			  let i = this.selectedIndex;
			  let text = this.textBoxArray[i].value;
				let convertedText = this.convertNumberToArabic(text);
				this.textBoxArray[i].value = convertedText;
		}
		else {
			// otherwise change all lines	
			if (confirm("Convert all numbers on page to Arabic form?")){
				for (var i=0;i<this.textBoxArray.length;++i) {
					let text = this.textBoxArray[i].value;
					let convertedText = this.convertNumberToArabic(text);
					this.textBoxArray[i].value = convertedText;
    			}
    		}
    	}
	}
    
    get_text(lineIndices) {
        let text = '';
        for (let i of lineIndices) {
            text += this.textBoxArray[i].value + '\n';
        }
        return text;
        
    }
    
    
    get_all_text() {
        let text = '';
        for (let i=0;i<this.textBoxArray.length;++i) {
            text += this.textBoxArray[i].value + '\n';
        }
        return text;
        
    }
    //called when right page's line is clicked
    showTextBox(index) {
        if (index < 0 || index >= this.textBoxArray.length) {
            //if invalid then show all textboxes
            for (var i=0;i<this.textBoxArray.length;++i) 
                this.textBoxArray[i].style.visibility = "visible";
                return
        }
        for (var i=0;i<this.textBoxArray.length;++i) {
			this.textBoxArray[i].style.visibility = "hidden";
        }
        this.textBoxArray[index].style.visibility = "visible";
        
    }


} //end of class transcribeBlock

// This class has line annotations + buttons for marking/tagging regions
class tagBlock extends annotateBlock {
  constructor(imageWidth, canvasId="imgCanvas", imageId="manuscript") {
    super(imageWidth, canvasId, imageId);
  	this.tagButtonArray = 0;  
  	// This holds a map of all buttons that link them to an index
  	// The index is for the associated lineArray
  	this.tagButtonMap = new Map();
  	this.openButtonIndex = -1;
    
  }

  // for a particular line, get the top left coordinates of button
  getButtonTopLeft(lineIndex) {
  	var canvasRect = this.canvas.getBoundingClientRect();
  	var minX, minY, maxX, maxY;
  	[minX, minY, maxX, maxY] = this.lineArray[lineIndex].getCornerPts();
    // Find closest polygon point to (minX, maxY)
    let pt =  this.lineArray[lineIndex].getClosestPoint(new myPoint(minX, minY))
    minX = pt.x;
    minY = pt.y;

  	var left = canvasRect.left + minX + window.scrollX; //  + 'px';
  	var top = canvasRect.top + minY + window.scrollY; // + 'px';


  	var pos={'left': left, 'top':top};
  	return pos;

  }

  // If tag dictionary is present in Json, it would be passed here. Otherwise tagDict is none
  addItemToTags(ul, text, tagDict, uniqueId){
    ul.style.cssText = "list-style-type:none;border: 1px solid #ddd;width:200px";    
    var li = document.createElement('li');//li

    var checkbox = document.createElement('input');
    checkbox.type = "checkbox";
    checkbox.value = text;
    checkbox.name = text;
    checkbox.id = TAG_CHECKBOX_ID + '-' + uniqueId + '-' + text;;
    //Check if text is in tagDict
    if (tagDict != null && text in tagDict){
    	checkbox.checked = (tagDict[text] == 1);
    }
    checkbox.addEventListener("click", onTagCheckBoxClicked)

    var label = document.createElement('label');
    var textNode = document.createTextNode(text);
    
    label.appendChild(checkbox);
    label.appendChild(textNode);
    label.htmlFor = checkbox.id;
    
    li.appendChild(label);   
    
    ul.appendChild(li); 
}


	// create a unique id and use it to create more ids
  // for button, list, checkbox items
  createTagButton(position, index, tagDict) {
	  
	  var uniqueId =  Date.now() + parseInt(Math.random()*1e6); //Hopefully a unique id
	  var button = document.createElement("button");
        
    
    //button.style.position = 'absolute';
	  //button.style.top = (position.top - 20) + "px";
	  //button.style.left = (position.left - 20) + "px";
    //Assign different attributes to the element. 
      button.type = "button";
      button.class = "btn btn-link btn-sm"; 
      button.setAttribute("data-bs-toggle", "collapse"); 
      button.id = 'button-' + uniqueId;
      //button.style = "padding:0px;border:1px solid #ddd";
      button.style.color = "black";
      button.setAttribute("data-bs-target", "#" + 'tagList-' + uniqueId) ;
	  // create the collapse div
    var collapseDiv = document.createElement('div');
    collapseDiv.style.minHeight = "120px";
    collapseDiv.className = 'collapse collapse-horizontal';
    collapseDiv.id = 'tagList-' + uniqueId;

    // create the card div with the list inside
    var cardDiv = document.createElement('div');
    cardDiv.className = 'card card-body';

    var ul = document.createElement('ul');
    var tagged = false;
    for (var i=0;i<TAG_ITEMS.length;++i) {
    	var item = TAG_ITEMS[i];
        this.addItemToTags(ul, item, tagDict, uniqueId);
        if (tagDict[item] == 1) tagged = true;
    }

    //Change button according to tags
    this.setTaggedButtonStyle(button, tagged);
    cardDiv.appendChild(ul);
    collapseDiv.appendChild(cardDiv);


    // Create the container div
    var containerDiv = document.createElement('div');

    containerDiv.id = TAG_DIV_CONTAINER + uniqueId

    // Append the button and the collapse div to the container div
    containerDiv.appendChild(button);
    containerDiv.appendChild(collapseDiv);

    containerDiv.style.position = 'absolute';
	  containerDiv.style.top = (position.top - 25) + "px";
	  containerDiv.style.left = (position.left - 25) + "px";
    document.body.appendChild(containerDiv);
    
    //button.addEventListener("click", tagButtonClicked);

	  return button;
	}
	closeOpenBoxes(index) {
		if (this.openButtonIndex < 0 || this.openButtonIndex >= this.lineArray.length)
			return false;
		if (index == this.openButtonIndex)
			return false;

		var button = this.tagButtonArray[this.openButtonIndex];

		var tagListId = button.getAttribute('data-bs-target').slice(1);

		var tagList = document.getElementById(tagListId);


		if (tagList.classList.toggle("show"))
			tagList.classList.toggle("show");
		this.openButtonIndex = -1;
	}

	// To discard
	onTagButtonClicked(event) {
		
		var button = event.delegateTarget;
		event.preventDefault();
		var index = this.tagButtonMap.get(button);
		if (index < 0)
			return;
		//some other line already selected
		if (this.getSelectedIndex() >= 0 && index != this.getSelectedIndex())
			return;

		var tagListId = button.getAttribute('data-bs-target').slice(1);

		var tagList = document.getElementById(tagListId);
		this.closeOpenBoxes(index);
		if (tagList.classList.toggle("show"))
			this.openButtonIndex = index;
		else
			this.openButtonIndex = -1;

			

		
		super.changeSelectedIndexForView(index);
	}

  initializeLines(linesJson) {
  	var minX, maxX, minY, maxY;
  	var tagDict = null;
  	super.initializeLines(linesJson);
  	
  	
  	var minX=0, maxX=0, minY=0, maxY=0;
		
  	this.tagButtonArray = new Array(this.lineArray.length);
  	for (var i=0;i<this.tagButtonArray.length;++i) {
  		tagDict = this.lineArray[i].tagDict;
  		var pos = this.getButtonTopLeft(i);
  		var button = this.createTagButton(pos, i, tagDict);   
  		this.tagButtonArray[i] = button;
		this.tagButtonMap.set(button, i);
			//document.body.appendChild(button);
			
  	}

  }
  setTaggedButtonStyle(button, tagged) {
      if (!tagged) {
        button.innerHTML = BUTTON_TEXT_NO_TAG;
        button.style.color = NORMAL_COLOR;
        //button.style.background = NORMAL_COLOR;
      }
      else {
        button.innerHTML = BUTTON_TEXT_TAG;
        button.style.color = TAGGED_STROKE_COLOR;      
        //button.style.background = NORMAL_COLOR;    
      }
  }

  onTagCheckBoxClicked(event) {
  	let vertical = false;
		// checkbox id has index of line and list item
		var id = event.target.id;
		if (!id.includes(TAG_CHECKBOX_ID))
			return [-1, false];
		var uniqueId = id.substring(id.indexOf('-') + 1, id.lastIndexOf('-'));
		
		// Find the index of button in tagButtonArray
		var button = document.getElementById('button-'+uniqueId);
		if (!button) {
			alert('Could not find the parent element for checkbox');
			return [-1, false];
		} 

		var index = this.tagButtonMap.get(button);
		if (index < 0 || index >= this.lineArray.length) {
			alert('Could not find the index for checkbox');
			return [-1, false];
		}

		var key = event.target.value;
		this.lineArray[index].tagDict[key] = +event.target.checked;
    // Set button styles
    if (event.target.checked) {
        this.setTaggedButtonStyle(button, true);
    }
    else {
        var tagged = this.lineArray[index].isTagged();
        this.setTaggedButtonStyle(button, tagged);
        
    }

    if (this.lineArray[index].isVerticalOrientation())
    	vertical = true;

    return [index, vertical];
            
  }



	

  reinitialize(linesJson, widthImg) {
  	super.reinitialize(linesJson, widthImg);
  	var minX, maxX, minY, maxY;

  	for (var i=0;i<this.tagButtonArray.length;++i) {
  		//var position = this.textBoxArray[i].getBoundingClientRect();
  		var pos = this.getButtonTopLeft(i);
  		var left = pos.left;
  		var top = pos.top;
  		var containerDiv = this.tagButtonArray[i].parentNode;
  		containerDiv.style.position = 'absolute';
	  	containerDiv.style.top = top + "px";
	  	containerDiv.style.left = left + "px";
  	} 	
  }
    // Overloading
	setNormalMode() {
		var minX, maxX, minY, maxY;
		var canvasRect = this.canvas.getBoundingClientRect(); 
		var index = -1;
		if (this.lineChanging != -1) {
			index = this.lineChanging;
		}
  	
  	if (index < 0 || index >= this.lineArray.length) {
  		super.setNormalMode();
  		return;
  	}

  	var position = this.getButtonTopLeft(index);
  	var left = position.left;
  	var top = position.top;
  	
	var containerDiv = this.tagButtonArray[index].parentNode;
	containerDiv.style.position = 'absolute';
  	containerDiv.style.top = top + "px";
  	containerDiv.style.left = left + "px";
	
  	super.setNormalMode();

  	if (SHOW_TAGS) {
  		this.showTags(true);    
  	}
  	else {
  		this.showTags(false); 
  	}

  }

  //opverloading
  onPencilClick() {
      
    //Cannot draw in edit mode
    if (this.editing)
      return;  
    //Hide all buttons
    this.showTags(false);    
    super.onPencilClick();
    
  }

  //overloading
  pencilDoubleClick(event) {
  	let totalLines = this.lineArray.length;
  	super.pencilDoubleClick(event);
  	this.showTags(SHOW_TAGS);
  	// Was line added
  	let lastIndex = this.lineArray.length - 1;
  	//Check if line was added
  	if (lastIndex != totalLines) 
  		return;

  	//Add the tag button
  	var tagDict = this.lineArray[lastIndex].tagDict;
  	var pos = this.getButtonTopLeft(lastIndex);
  	var button = this.createTagButton(pos, lastIndex, tagDict);   		
  	this.tagButtonArray[lastIndex] = button;
		this.tagButtonMap.set(button, lastIndex);
		if (!SHOW_TAGS) {
			this.tagButtonArray[lastIndex].parentElement.classList.add("invisible");
		}

  }

//overloaded
pasteClicked() {
	let totalLines = this.lineArray.length;
	super.pasteClicked();
	// Was line added
  	let lastIndex = this.lineArray.length - 1;
  	//Check if line was added
  	if (lastIndex != totalLines) {
  		return;
  	}

  	//Add the tag button
  	var tagDict = this.lineArray[lastIndex].tagDict;
  	var pos = this.getButtonTopLeft(lastIndex);
  	var button = this.createTagButton(pos, lastIndex, tagDict);   
  	this.tagButtonArray[lastIndex] = button;
		this.tagButtonMap.set(button, lastIndex);
		if (!SHOW_TAGS) {
			this.tagButtonArray[lastIndex].parentElement.classList.add("invisible");
		}
  	
	}


  deleteLine() {
      	let index = this.selectedIndex;
      	if (index < 0 || index >= this.lineArray.length)
      		return -1;
    
      	var button = this.tagButtonArray[index];
      	var divContainer = button.parentNode;
      	while (divContainer.firstChild) {
      		divContainer.removeChild(divContainer.lastChild);
      	}
      	divContainer.remove();
    
      	this.tagButtonArray.splice(index, 1);
    
      	//update map
      	for (var i=index;i<this.tagButtonArray.length;++i)
    			this.tagButtonMap.set(this.tagButtonArray[i], i);
    
      	index = super.deleteLine();
      	return index;
  }

  //overloaded
  setMoveMode() {
  	super.setMoveMode();
  	this.showTags(false);
  } 

  //overloaded
  setEditMode() {
  	super.setMoveMode();
  	this.showTags(false);
  }
  

  // called on mouse move
  //overloaded function to show tags added
  changeColors(ctx, x, y){
    ctx.save();
    //we may have more than one selected
    for (let i = 0;i < this.lineArray.length; ++i){
      if (this.lineArray[i].isRegion() && !this.showRegions)
          continue;
      const isPointInPoly = this.lineArray[i].isPointInPath(ctx, x, y);
      if (isPointInPoly) {
          ctx.fillStyle = MOVE_STYLE;
          
          this.lineArray[i].fill(ctx);
          this.lineArray[i].stroke(ctx);   
          this.tagButtonArray[i].style.background = SELECTED_BUTTON_BK_COLOR;
      }    
    } //end for
    ctx.restore();
  }
    
  changeTaggedLineRegionColors(ctx, lineInd) {
    var key, value;
    for (key in REGION_KEYS) {
          var k = REGION_KEYS[key];
          if (this.lineArray[lineInd].tagDict[k]) {
              ctx.fillStyle = TAG_DICTIONARY[k]; //REGION_FILL_COLOR;
              this.lineArray[lineInd].fill(ctx);
              //this.tagButtonArray[i].style.color = TAGGED_STROKE_COLOR;
              if (lineInd < this.tagButtonArray.length)
                  this.tagButtonArray[lineInd].style.background = NORMAL_BUTTON_BK_COLOR;
              break //color according to first tag encountered
          }
          
      } //change stroke color if tag assigned
      for ([key, value] of Object.entries(TAG_DICTIONARY)) {
          
          if (this.lineArray[lineInd].tagDict[key]) {
            ctx.strokeStyle = TAGGED_STROKE_COLOR;
            this.lineArray[lineInd].stroke(ctx);
              
            if (lineInd < this.tagButtonArray.length)
                this.tagButtonArray[lineInd].style.background = NORMAL_BUTTON_BK_COLOR;

            if (key.startsWith('Region')) {
                  ctx.fillStyle = TAG_DICTIONARY[key];//REGION_FILL_COLOR;
                  this.lineArray[lineInd].fill(ctx);
            } // end if key.startsWith ...
            break;  //break if tag found
          } //end outer most if
      }      //end for iterating on object.entries
      
  }

  // Overloading to show tagged areas
  refreshLines() {
    let ctx = this.canvas.getContext("2d");
    ctx.save();
    for (let i=0;i<this.lineArray.length;++i) {
      // First check if region shoujld be filled
      var tagged = this.lineArray[i].isTagged();
      var isRegion = this.lineArray[i].isRegion();
      if ((isRegion && this.showRegions) || (!isRegion && tagged)) {
          this.changeTaggedLineRegionColors(ctx, i);

      }
      
      if (!tagged) {
          // If no tag selected
          ctx.strokeStyle = "black";
          this.lineArray[i].stroke(ctx);
          
          if  (i < this.tagButtonArray.length)
              this.tagButtonArray[i].style.background = NORMAL_BUTTON_BK_COLOR;
      } //end if !tagged
    }    //end  for loop
    ctx.restore();
  } //end refresh lines

  showTags(show){
      for (var i=0;i<this.tagButtonArray.length;++i) {
        if (show) {
        	//making the parent div container invisible/visible to avoid mouse clicks going there
        	this.tagButtonArray[i].parentElement.classList.remove("invisible");
        }
        else {
            this.tagButtonArray[i].parentElement.classList.add("invisible");
        }
    }
  }

} //end of class tagBlock




function onTagCheckBoxClicked(event) {
	let [index, vertical] = RIGHT_PAGE.onTagCheckBoxClicked(event);

	if (vertical) {
		let line = RIGHT_PAGE.getLine(index);
		LEFT_PAGE.changeLine(index, line);
	}


}

function onTagDivBlur(event) {
		button = event.target;
		listId = button.getAttribute("data-bs-target");
		listId = listId.slice(1);
		//Dont know how else to do this. If already visible then hide it
		if (document.getElementById(listId).classList.toggle("show"))
			document.getElementById(listId).classList.toggle("show");

	}

function appendImg(img_src, id) {
	img_node = document.createElement("IMG");
	img_node.id = id;
	img_node.src = img_src;
	img_node.hidden = true;
	document.body.appendChild(img_node);
}

function fill_select_json_files(json_obj) {
	let leftSelect = document.getElementById("leftSelect")
	// Left side selection
	for (let i=0;i<json_obj.fileList.length;++i) {
      let opt = document.createElement("option");
      opt.innerHTML = json_obj.fileList[i];
      leftSelect.appendChild(opt);      
  }
  leftSelect.selectedIndex = 0;
}

function fill_htr_models_listbox(models, selected_index) {
    let modelSelect = document.getElementById("HTRModelSelect")
    for (let i=0;i<models.length;++i) {
        let opt = document.createElement("option");
        opt.innerHTML = models[i];
        modelSelect.appendChild(opt);
    }
    modelSelect.selectedIndex = selected_index;
}

function initPage(leftImg, rightImg, jsonObj){

  if ("textbox_ht" in ADMIN)
      TEXTBOX_HT = ADMIN.textbox_ht
	// Make the relevant button visible
  if (!CHECKING) {
    var button = document.getElementById("checkTranscript");
    button.style.display = "none";
  }
  else {
    var button = document.getElementById("submitTranscript");
    button.style.display = "none";
  }
    
  if (OPTIONS["show_HTR"] != 1)
  {
      document.getElementById("PageHTR").style.display = "none";
      document.getElementById("LineHTR").style.display = "none";
      document.getElementById("HTRModelSelect").style.display = "none";
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
	let widthImg = getImageWidth();
	LEFT_PAGE = new transcribeBlock(widthImg, "leftCanvas", "leftSideImage");
	RIGHT_PAGE = new tagBlock(widthImg, "rightCanvas", "rightSideImage");

	//Set the select options
	fill_select_json_files(jsonObj);
    //Fill models
    fill_htr_models_listbox(HTR.models, OPTIONS.HTR_model_ind);
	// If no json object then create a dummy json
	// handleEmptyJson();
  makeDefaultSelections();
  addEventListeners();
  //LEFT_PAGE.changeSelectedIndex(0);
 if (OPTIONS["is_public_user"] == 1) {
          document.getElementById("submitTranscript").innerText = "Delete File";
      }   
    //move the contrast slider
  const slider = document.getElementById('contrastRange');
  slider.value = LEFT_PAGE.contrastValue;  
  let showRegions = OPTIONS["show_regions"] != 1; //opp will be set up in onShowRegions
  LEFT_PAGE.showRegions = showRegions;
  RIGHT_PAGE.showRegions = showRegions;
  onShowRegions(); 
  //check if download request was sent
  if ("downloadText" in OPTIONS && OPTIONS["downloadText"] == 1) {
      onDownload(false, jsonObj[JSON_FILE]['json']['text'])
  }
  
}

function addEventListeners() {
	rightCanvas = document.getElementById("rightCanvas");
	rightCanvas.addEventListener("mousemove",onMouseMove);
  rightCanvas.addEventListener("mousedown",onMouseDown);
  rightCanvas.addEventListener("mouseup",onMouseUp);
  leftCanvas.addEventListener("mousemove", onMouseMove)
  document.addEventListener("click", onMouseClick);
  document.addEventListener("keydown", onKeyDown);
  document.addEventListener("lineAdded", onAddLine);
  //document.addEventListener("lineChangedEvent", onChangeLine);
  window.addEventListener("resize", onWindowResize);

	rightCanvas.addEventListener('mouseenter', function() {
  	MOUSE_IN_RIGHT_CANVAS = true;
	});

	rightCanvas.addEventListener('mouseleave', function() {
  	MOUSE_IN_RIGHT_CANVAS = false;
	});

 
}

// To correct the problem with moving annotation
function getImageWidth() {
	let widthLeft = leftCanvas.getBoundingClientRect().width;
	let widthRight = rightCanvas.getBoundingClientRect().width;
	if (widthLeft != widthRight)
		alert("widths are not equal");
	return Math.min(widthLeft, widthRight);
}


function onWindowResize() {
	//alert("window resized");
	//Get all the updated lines before moving the canvas
	let jsonObject = JSON.parse(LEFT_PAGE.getJsonString());
	let widthImg = getImageWidth();
	RIGHT_PAGE.reinitialize(jsonObject, widthImg);	
	LEFT_PAGE.reinitialize(jsonObject, widthImg);
}

function onMouseMove(event) {

	MOUSE_X = event.clientX;
  MOUSE_Y = event.clientY;

	if (event.target.id == "rightCanvas")
		RIGHT_PAGE.onMouseMove(event);

	else if (event.target.id == "leftCanvas" && RIGHT_PAGE.zoomOn) {
		mousePosition = new myPoint(event.offsetX, event.offsetY);
		RIGHT_PAGE.fillZoomBox(mousePosition);
	}
}

function onMouseDown(event) {
	if (event.target.id == "rightCanvas")
		RIGHT_PAGE.onMouseDown(event);
}

function onMouseUp(event) {
  if (event.target.id == "rightCanvas")
	  RIGHT_PAGE.onMouseUp(event);
}

function onKeyDown(event) {

	rightCanvas = document.getElementById("rightCanvas");
	const canvasBounds = rightCanvas.getBoundingClientRect();
	if (!MOUSE_IN_RIGHT_CANVAS)
		return;
  //This shoudl delete selected line
  if (event.key == "Delete" || event.key == "Backspace")
    onDeleteButton();  
  //This should start draw mode
  else if (event.key == '+')
    onDrawButton();
  //this is to delete a control point
  else if (event.key == '-')
    RIGHT_PAGE.onMinusPressed();
  //this is to add a control point
  else if (event.key == 'p')
    RIGHT_PAGE.onAddControlPointPressed();  
  // copy for paste later
  if ((event.key == 'c') && event.ctrlKey)
    RIGHT_PAGE.copyClicked();
  //for pasting after copy
  else if ((event.key == 'v') && event.ctrlKey)
    RIGHT_PAGE.pasteClicked();  

  document.getElementById("rightCanvas").tabIndex = 1;
}

function pointInBounds(rect, x, y) {
	return x >= rect.left && x <= rect.right && y >= rect.top && y <= rect.bottom
}


function onMouseClick(event) {

	let leftCanvas = document.getElementById("leftCanvas")
	const canvasBounds = leftCanvas.getBoundingClientRect();
	const mouseX = event.clientX;     //incorrect to subtract- canvasBounds.left;
  const mouseY = event.clientY; //- canvasBounds.top;
  
	
  //if right page clicked
	if (event.target.id == "rightCanvas") {
	  if (event.detail == 2) {
  	  RIGHT_PAGE.onMouseDoubleClick(event);
    	
  	}
  	else if (event.detail == 1)
    	RIGHT_PAGE.onMouseClick(event);
        index = RIGHT_PAGE.getSelectedIndex();
        LEFT_PAGE.showTextBox(index);
  }
	//else if draw button clicked	
	else if (event.target.id == "drawButton") {
		onDrawButton();
	
	}
	else if (pointInBounds(canvasBounds, mouseX, mouseY)) {  	
		//subtract here to get relative position
		LEFT_PAGE.MouseClick(mouseX - canvasBounds.left, mouseY- canvasBounds.top);
		index = LEFT_PAGE.getSelectedIndex();
		RIGHT_PAGE.restoreNormal(index);
  }
  
}


// Event for text area
function keyUpEvent(event) {

	if (event.key == 'Enter' && LINE_BY_LINE) {
		LEFT_PAGE.inputEndKeyPressed();
		event.stopPropagation();

		index = LEFT_PAGE.getSelectedIndex();
		RIGHT_PAGE.changeSelectedIndexForView(index);
	}

	if ((event.key == 'Escape') || (event.key == 'Tab'))	{
		LEFT_PAGE.inputEndKeyPressed();
		event.stopPropagation();

		index = LEFT_PAGE.getSelectedIndex();
		RIGHT_PAGE.changeSelectedIndexForView(index);
		
	}
}

function tagButtonClicked(event) {
	RIGHT_PAGE.onTagButtonClicked(event);
}


// Event for text area
function onTextAreaFocus(event) {
	LEFT_PAGE.onTextAreaFocus(event);
}

function onTextAreaBlur(event) {
	LEFT_PAGE.onTextAreaBlur(event);
}	



function postViewForm(flag) {

	if (LEFT_PAGE.canvas.height == 0 || RIGHT_PAGE.canvas.height==0)
        document.location.reload();


	if (flag < 1 || flag > 9)
        return;
  let submitForm = false;
  let checked = false;

  //Previous pressed
	if (flag == 1) {
		document.getElementById('tagInput').name='previous';
	}
	//next pressed
	else if (flag == 2) {
		document.getElementById('tagInput').name='next';
	}
    //save pressed
  else if (flag == 3) {
    document.getElementById('tagInput').name='save';
  }
    //end pressed
  else if (flag ==4) {
    document.getElementById('tagInput').name='end';
  }
	else if (flag == 5) {
		
    let confirmMessage = "Are you sure you want to submit this transcription?"
    if (OPTIONS["is_public_user"] == 1) {
        confirmMessage = "Are you sure you want to delete this transcription? You won't see it again in this pool after deleting."
    }
    if (!confirm(confirmMessage)) {
    		
        document.getElementById('tagInput').name='save';
      }
    	// Submit clicked
    	else {
	    	document.getElementById('tagInput').name='submitForm';
      	submitForm = true;
      }
      
  }
  else if (flag == 6) {
  	
    if (!confirm("Save this transcription as checked?")) {
    		
    		document.getElementById('tagInput').name='save';
        
      }  
      else {
    	// checked clicked
    	document.getElementById('tagInput').name='checked';
    	checked = true;
      }
  }
    
    // For page HTR
    else if (flag == 7) {
    	document.getElementById('tagInput').name='pageHTR';

    }

    // For line HTR
    else if (flag == 8) {
    	document.getElementById('tagInput').name='lineHTR';
    }
    
    else if (flag == 9) {
        document.getElementById('tagInput').name='getSortedJson';
    }
    

  
  let selectedLineIndex = RIGHT_PAGE.selectedIndex;
  let HTR_model_ind = document.getElementById("HTRModelSelect").selectedIndex;
  if (HTR_model_ind < 0) HTR_model_ind = OPTIONS["HTR_model_ind"]

  let options = {"radius": RADIUS, "lineWidth": DRAW_LINE_WIDTH, 
  				"zoomFactor": ZOOM_FACTOR, 
  				"colWidth": COL_WIDTH, 
                "selectedLineIndex": selectedLineIndex,
                "show_HTR": OPTIONS["show_HTR"], 
                "show_tags": SHOW_TAGS ? 1 : 0,
                "HTR_model_ind": HTR_model_ind,
                "is_public_user": OPTIONS["is_public_user"],
                "htr_in_progress": 0,
                "show_regions": RIGHT_PAGE.showRegions ? 1 : 0}
  let scrollPosition = getScrollPosition();
  let image_name = document.getElementById("rightImageName").innerHTML
  let jsonToPost = {"images_obj": IMAGES, "admin": ADMIN, 
                     "page_json": LEFT_PAGE.getJsonString(submitForm, checked),
                     "json_file": JSON_FILE,
                     "scroll_position": {"x": scrollPosition.x, "y": scrollPosition.y},
                     "task_id": HTR.task_id,
                     "options":options};

  document.getElementById('tagInput').value= JSON.stringify(jsonToPost);
  document.getElementById('tagForm').submit();
}

function postToCheckStatus(flag) {
    if (flag == 7) {
    	document.getElementById('tagInput').name='pageHTR';

    }

    // For line HTR
    else if (flag == 8) {
    	document.getElementById('tagInput').name='lineHTR';
    }
    else { return;}

  let HTR_model_ind = document.getElementById("HTRModelSelect").selectedIndex;
  if (HTR_model_ind < 0) HTR_model_ind = OPTIONS["HTR_model_ind"]
  let options = {"radius": RADIUS, "lineWidth": DRAW_LINE_WIDTH, 
  		"zoomFactor": ZOOM_FACTOR, 
  	        "colWidth": COL_WIDTH, 
                "selectedLineIndex": OPTIONS["selectedLineIndex"],
                 "show_HTR": OPTIONS["show_HTR"] ? 1 : 0,
                 "show_tags": SHOW_TAGS ? 1 : 0,
                 "HTR_model_ind": HTR_model_ind,
                 "is_public_user": OPTIONS["is_public_user"],
                 "htr_in_progress": 1,
                 "show_regions": RIGHT_PAGE.showRegions ? 1: 0}
  
  let image_name = IMAGE_FILENAME
  let jsonToPost = {"images_obj": IMAGES, "admin": ADMIN, 
                     "page_json": JSON.stringify(INPUT_JSON[INPUT_JSON.fileList[0]].json),
                     "json_file": INPUT_JSON.fileList[0],
                     "scroll_position": {"x": SCROLL_POSITION.x, "y": SCROLL_POSITION.y},
                     "task_id": HTR.task_id,
                     "options":options};

  document.getElementById('tagInput').value = JSON.stringify(jsonToPost);  
  document.getElementById('tagForm').submit();

}



function handleEmptyJson() {
	let selectedFile = document.getElementById("leftSelect");
  let ind = selectedFile.selectedIndex;
  filename = selectedFile.options[ind].innerHTML;
	let linesJson = JSON_OBJ[filename];
	let totalLines = 0;
	for (var key in linesJson){
      if (!key.startsWith("line"))
        continue;
      if ("deleted" in linesJson[key] && linesJson[key].deleted == "1")
        continue;
      totalLines += 1;
  }
  // Commenting out this block.
  // Add a default box around the whole page for transcription
  //if (totalLines == 0) {
  //	image = document.getElementById("leftSideImage");
  //	ht = this.image.naturalHeight;
  //	width = this.image.naturalWidth;

  //	linesJson = {"line_1":{"coord": [0, 0, 0, ht-1, width-1, ht-1, width-1, 0]}};
  //	JSON_OBJ[filename] = linesJson;
  //}

}

function makeDefaultSelections() {
    let selectedFile = document.getElementById("leftSelect");
    let ind = selectedFile.selectedIndex;
    filename = selectedFile.options[ind].innerHTML;
    LEFT_PAGE.refreshManuscript();
    LEFT_PAGE.initializeLines(JSON_OBJ[filename]['json']);    
    RIGHT_PAGE.initializeLines(JSON_OBJ[filename]['json']);
    JSON_FILE = filename;
    RIGHT_PAGE.showTags(SHOW_TAGS);
    RIGHT_PAGE.refreshManuscript();


}


function onleftListBoxSelectJson() {
    let selectedFile = document.getElementById("leftSelect");
    let ind = selectedFile.selectedIndex;
    filename = selectedFile.options[ind].innerHTML;
    
    document.getElementById("leftColumn").className = 'col-md-' + COL_WIDTH;
	document.getElementById("rightColumn").className = 'col-md-' + COL_WIDTH;	
	let widthImg = getImageWidth();
	LEFT_PAGE.initializeLines(JSON_OBJ[filename]['json']);    
    RIGHT_PAGE.initializeLines(JSON_OBJ[filename]['json']);
    JSON_FILE = filename;
    RIGHT_PAGE.showTags(SHOW_TAGS);    
}


function onDrawButton() {
	
	RIGHT_PAGE.onPencilClick();
}

function onAddLine() {
	scrollPosition = getScrollPosition();

	line = RIGHT_PAGE.getLastLine();
	LEFT_PAGE.addLine(line);

	window.scrollTo(scrollPosition.x, scrollPosition.y);


}

function onChangeLine(event) {

	
	let scrollPosition = getScrollPosition();
	let index = event.detail.lineIndex;
	let line = RIGHT_PAGE.getLine(index);
	LEFT_PAGE.changeLine(index, line);
	window.scrollTo(scrollPosition.x, scrollPosition.y);
	
	//document.getElementById("log").innerHTML = LEFT_PAGE.getJsonString();
	//document.getElementById("log0").innerHTML = RIGHT_PAGE.getJsonString();
}

function onDeleteButton(event) {
    
    
	scrollPosition = getScrollPosition();
	if (!confirm("Are you sure you want to delete the line?")) {
		window.scrollTo(scrollPosition.x, scrollPosition.y);
		return;
	}
	let index = RIGHT_PAGE.deleteLine();
    if (index != -1)
    {  //delete from left page
	   LEFT_PAGE.deleteLine(index);
    }
	window.scrollTo(scrollPosition.x, scrollPosition.y);
} 

function getScrollPosition() {
	var scrollPosition = {
    x: window.pageXOffset || document.documentElement.scrollLeft,
    y: window.pageYOffset || document.documentElement.scrollTop
  };
  return scrollPosition;
}



function zoomPlusClicked() {
	//Get all the updated lines before moving the canvas
	let jsonObject = JSON.parse(LEFT_PAGE.getJsonString());
	COL_WIDTH++;
	document.getElementById("leftColumn").className = 'col-md-' + COL_WIDTH;
	document.getElementById("rightColumn").className = 'col-md-' + COL_WIDTH;
	let widthImg = getImageWidth();
	RIGHT_PAGE.reinitialize(jsonObject, widthImg);	
	LEFT_PAGE.reinitialize(jsonObject, widthImg);
    RIGHT_PAGE.showTags(SHOW_TAGS);  
	

}
function zoomMinusClicked() {
	//Get all the updated lines before moving the canvas
	let jsonObject = JSON.parse(LEFT_PAGE.getJsonString());
	COL_WIDTH--;
	document.getElementById("leftColumn").className = 'col-md-' + COL_WIDTH;
	document.getElementById("rightColumn").className = 'col-md-' + COL_WIDTH;	
	let widthImg = getImageWidth();
	RIGHT_PAGE.reinitialize(jsonObject, widthImg);	
	LEFT_PAGE.reinitialize(jsonObject, widthImg);
    RIGHT_PAGE.showTags(SHOW_TAGS);  
	
}

function closeModal() {
  const modal = document.getElementById('myModal');
  modal.style.display = 'none';
  RIGHT_PAGE.zoomClose();
}


function zoomBoxPlusClicked() {
	RIGHT_PAGE.zoomPlus();
}

function zoomBoxMinusClicked() {
	RIGHT_PAGE.zoomMinus();
}

function changeLineSize(event) {
	DRAW_LINE_WIDTH = Number(document.getElementById("lineSize").value)/5;
	event.stopPropagation();
}

function changeRadius(event) {
	RADIUS = Number(document.getElementById("radius").value);
	event.stopPropagation();

}

function onshowTagsButton() {
    if (SHOW_TAGS) {
        RIGHT_PAGE.showTags(false);
        showTagsButton.innerHTML = "Tags <i class='fa'> &#xf06e; </i>";
        SHOW_TAGS = false;
    }
    else {
        RIGHT_PAGE.showTags(true);
        SHOW_TAGS = true;
        showTagsButton.innerHTML = "Tags <i class='fa'> &#xf070; </i>"
        
    }
}

function onShowRegions() {

    if (RIGHT_PAGE.showRegions) {
      //  RIGHT_PAGE.showRegions(false);
        showRegionsButton.innerHTML = "Regions <i class='fa'> &#xf06e; </i>";
        RIGHT_PAGE.showRegions = false;
    }
    else {
     //   RIGHT_PAGE.showRegions(true);
        RIGHT_PAGE.showRegions = true;
        showRegionsButton.innerHTML = "Regions <i class='fa'> &#xf070; </i>"
        
    }
    // propagate
    LEFT_PAGE.showRegions = RIGHT_PAGE.showRegions;
}


function getSetOptions() {
	COL_WIDTH = OPTIONS['colWidth'];
	RADIUS = OPTIONS['radius'];
	DRAW_LINE_WIDTH = OPTIONS['lineWidth'];
	ZOOM_FACTOR = OPTIONS['zoomFactor']
	document.getElementById("lineSize").value = DRAW_LINE_WIDTH*5;
	document.getElementById("radius").value = RADIUS;


}

// Convert numbers to Arabic
function ConvertNumbers() {
	LEFT_PAGE.convertNumbers();
}


function onPageHTRButton() {
    
    if (confirm("This will do a full page HTR. All annotation and text changes will be lost. You can wait for HTR to complete or visit this page later to view OCR results.")) {
        document.body.style.cursor='wait'; 
        postViewForm(7);
    }

}

function onLineHTRButton() {    
    carryOn = true;
    if (RIGHT_PAGE.selectedIndex < 0 || RIGHT_PAGE.selectedIndex >= RIGHT_PAGE.lineArray.length) {
        carryOn = confirm("This will do an HTR of all lines. All text changes will be lost.")
        //alert('Please select a line for line HTR')
        //return
    }
        
    if (carryOn) {
        document.body.style.cursor='wait'; 
        postViewForm(8);
    }

}

function downloadText(filename, text) {
  const element = document.createElement("a");
  const blob = new Blob([text], { type: "text/plain" });
  element.href = URL.createObjectURL(blob);
  element.download = filename;
  document.body.appendChild(element); // Required for Firefox
  element.click();
  document.body.removeChild(element);
}

function getFilenameWithoutExtension(filePath) {
  const filename = filePath.split('/').pop();         // e.g. "file.name.jpg"
  const lastDotIndex = filename.lastIndexOf('.');
  return lastDotIndex !== -1 ? filename.slice(0, lastDotIndex) : filename;
}

function onDownload(postForm, text="") {
    
      if (postForm)
          postViewForm(9)
      else
      {
            let image_name = leftImageName.innerHTML;
            let filename = getFilenameWithoutExtension(image_name) + '.txt'
            downloadText(filename, text);
    
    
            //Now download the json
            let json_str = LEFT_PAGE.getJsonString(false, false)
            let json_filename = getFilenameWithoutExtension(image_name) + '.json'
            downloadText(json_filename, json_str);   

      }    
}

function updateContrast(value) {
  
  RIGHT_PAGE.updateContrast(value)
  LEFT_PAGE.updateContrast(value)
}

