function showSelectedFiles() {
	var fileDialog = document.getElementById("fileDialog");
	selectedFiles = document.getElementById("selectedFiles");
	selectedFiles.innerHTML = ""; // Clear existing file list
            
    var files = fileDialog.files;
    
    if (files.length > MAX_FILES) {
        alert("You can upload up to " + MAX_FILES + " files for today. Limit resets tomorrow.");
        return;
    }
    let alertText = 'Size too large for: ';
    let showAlert = false;
    for (var i = 0; i < files.length; i++) {
        if (files[i].size > FILE_SIZE_LIMIT) {
            alertText += files[i].name + ', ';
            showAlert = true;
        }
        else {
            var option = document.createElement("option");
            option.text = files[i].name;
            selectedFiles.add(option);
        }
    }
    if (selectedFiles.length > 0) {
    	document.getElementById("uploadButton").disabled = false;
    }
    if (showAlert) {
        alertText += '\n\n\n Maximum limit is ' + parseInt(FILE_SIZE_LIMIT/1024/1024) + 'MB';
        alert(alertText);
    }
}


function displayErrors(notDoneList, errorString) {
	if (errorString.length > 0) {
		alert(errorString);
	}
	if (notDoneList.length == 0) {
		return;
	}
	alert('Some files could not be uploaded. See error log below');

	logs = document.getElementById("errorLogs");
	logs.innerHTML = ""; // Clear existing list
            
    
    for (var i = 0; i < notDoneList.length; i++) {
    	var option = document.createElement("option");
        option.text = notDoneList[i].filename + ' ' + notDoneList[i].error;
        logs.add(option);
    }
}

function displayDone(doneList) {


    if (doneList.length == 0) {
		return;
	}
	alert('See list below for files successfully uploaded');

	let logs = document.getElementById("logs");
	logs.innerHTML = ""; // Clear existing list
            
    
    for (var i = 0; i < doneList.length; i++) {
    	var option = document.createElement("option");
        option.text = doneList[i];
        logs.add(option);
    }	
    document.getElementById("annotateButton").disabled = false;

}


    

// flag: 1 for annotate
function submitForm(flag) {
  if (flag == 1) {
      let logs = document.getElementById("logs");
      let filesList = new Array(logs.length);
      for (i=0;i<logs.length;++i) {
          filesList[i] = logs[i].text;
      }
      var toPostJson = {"job": USER, 
                        "fileList": filesList,
                        "annotate": 1};  
      document.getElementById('formInputId').value= JSON.stringify(toPostJson);
      document.getElementById('uploadForm').submit();  
  }
    
  
    
  
}