
//////table talmud
var talmud = [
    ["ברכות", 125],
    ["שבת", 312],
    ["עירובין",207],
    ["פסחים",240],
    ["שקלים",41],
    ["ראש השנה",67],
    ["יומא",173],
    ["סוכה",110],
    ["ביצה",78],
    ["תענית",59],
    ["מגילה",60],
    ["מועד קטן",55],
    ["חגיגה",51],

    ["יבמות",242],
    ["כתובות",222],
    ["נדרים",180],
    ["נזיר",130],
    ["סוטה",96],
    ["גיטין",178],
    ["קידושין",162],

    ["בבא קמא",236],
    ["בבא מציעא",235],
    ["בבא בתרא",350],
    ["סנהדרין",224],
    ["מכות",46],
    ["שבועות",96],
    ["עבודה זרה",150],
    ["הוריות",25],

    ["זבחים",238],
    ["מנחות",217],
    ["חולין",281],
    ["בכורות",119],
    ["ערכין",65],
    ["תמורה",65],
    ["כריתות",54],
    ["מעילה",41],
    ["קינין",17],
    ["תמיד",8],
    ["מדות",8],

    ["נדה",143]];

var thisMasechet =0;
var thisDaf = 0;


function start() {

    if ("thisMasecet" in localStorage) {
        thisMasechet= parseInt(localStorage.getItem('thisMasecet'));
    }
    if ("thisDaf" in localStorage) {
        thisDaf= parseInt(localStorage.getItem('thisDaf'));
    }

    tableTalmud();
    //tableMefasim() ;
    loadMasechet(thisMasechet,thisDaf);
    //showDivMasechtot()
    //LEFT: 37, UP: 38,  RIGHT: 39, DOWN: 40
    window.addEventListener("keydown", function(e){
        if(e.keyCode === 37 && document.activeElement !== 'text') {
            e.preventDefault();
            next();
        }
        if(e.keyCode === 39 && document.activeElement !== 'text') {
            e.preventDefault();
            back();
        }
        if(e.keyCode === 38 && document.activeElement !== 'text') {
            e.preventDefault();
            //togglebt();
        }
        if(e.keyCode === 40 && document.activeElement !== 'text') {
            e.preventDefault();
            //togglebt();
        }
    });
    const el = document.getElementById('mefarshim-bt');
    el.addEventListener("click", () => tableMefasim());
    const el2 = document.getElementById('text-gmara-bt');
    el2.addEventListener("click", () => loadDafText(thisMasechet,thisDaf));
 }
 


function tableTalmud() {

   var row = 0;
   var cols = 0;
   var len = talmud.length;
   for (var i=0; i<len; i++)
    {
      makeDir("cal",i,talmud[i][0],function () {
            //window.location.assign("masechet.html?no=" + this.id);
            //showDivDaf(this.id);
            loadMasechet(this.id,0);
            localStorage.setItem('thisMasecet', this.id);

        },cols,row,"shas")

      cols++;
      if(cols == 5) {row++; cols =0;}
    }


}

function makeDir(name, id, conect,click, column, row, tableID) {

     var div = document.createElement("div");
     div.className = name;
     div.id = id;
     div.appendChild(document.createTextNode(conect));
     //console.log(conect);
     div.onclick = click;

     var tbl = document.getElementById(tableID);
     if(tbl) {tbl.rows[row].cells[column].appendChild(div);}

     return div;
 }

 /*
 function makeNewTab(text) {

   var tab = '<label id=' + text +' class="topcoat-tab-bar__item">' +
	  '<input type="radio" name="topcoat" class="hide-input">' +
	  '<button'  +
          //onclick='showMasechtot()' +
          ' class="topcoat-tab-bar__button">' + text + '</button></label>'
         document.getElementById("tab-bar").innerHTML += tab;

 }
 */

 /*
function  showDivMasechtot() {
   var masechtot = document.getElementById("masecet-show");
   var daf = document.getElementById("daf-show");

   masechtot.style.display = 'block'
   daf.style.display = 'none'

   tableTalmud();
}

function  showDivDaf(n_masechet) {
   //var masechtot = document.getElementById("masecet-show");
   //var daf = document.getElementById("daf-show");

   //daf.style.display = 'block';
   //masechtot.style.display = 'none';

   loadMasechet(n_masechet);

}
*/
////
var folder = 0;

/*
function getUrlVars() {
    var vars = {};
    var parts = window.location.href.replace(/[?&]+([^=&]+)=([^&]*)/gi, function(m,key,value) {
        vars[key] = value;
    });
    return vars;
}
*/

function loadMasechet(n_masechet, n_daf){
    //folder =  getUrlVars()["no"];

    loadDaf(n_masechet, n_daf);
    makeList(n_masechet);
    //makeNewTab(talmud[n_masechet][0]) ;
    document.title = talmud[n_masechet][0];
    //alert(talmud[n_masechet][0]);
   // tableMefasim();

 }


function loadDaf(n_masechet, n_daf){

   var daf = document.getElementById("daf");
   var daftext = document.getElementById("daf-text");

   daf.src = "shas/" + n_masechet + "/" + n_daf + ".pdf#toolbar=0&view=FitH"
   daftext.src = "shastext/gmara1/" + n_masechet + "/" + n_daf + ".html"

   thisMasechet = n_masechet;
   thisDaf = n_daf;
   localStorage.setItem('thisDaf', thisDaf);


   var src = daf.src;
   var s = src.substring(src.lastIndexOf('/')+ 1);
   var name = s.split('.')[0];
   var i = parseInt(name) ;

   if (n_daf == 0) {
    $(".bi-chevron-right").hide();
    }else {$(".bi-chevron-right").show();};


    if (n_daf == talmud[n_masechet][1]-1) {
        $(".bi-chevron-left").hide();
    }else {$(".bi-chevron-left").show();};

   if(i % 2 == 0 )
  {
   daf.style.borderRight = "20px solid #e9ebf0";
   daf.style.borderLeft = "2px solid #e9ebf0";
   //daf.style.borderImage = "linear-gradient(to right, darkblue, darkorchid) 1";
  }
  else {
   daf.style.borderLeft = "20px solid #e9ebf0";
   daf.style.borderRight = "2px solid #e9ebf0";

  }

 }

 var gmaraTextJson = {}

 function loadDafText1(n_masechet, n_daf){

 }
 

 function loadDafText(n_masechet, n_daf){
    //console.log(n_masechet + "-" + n_daf);
    var nn_daf = parseInt(n_daf);
    var path = window.location.href.replace('index.html', '');
    document.getElementById("title-daf-gmara").innerHTML = a(nn_daf);

    var myIFrame = document.getElementById("daf-text");
    var content = myIFrame.contentWindow.document.body.innerHTML;
    //var dafText = document.getElementById("con-text-gmara");
   // dafText.innerHTML = content;


/*
    $.getJSON(path + "shastext/gmara/" + n_masechet + ".json", function(result){

        var t1 = result["textR"] ? result.textR[nn_daf+2] : "";
        //console.log(nn_daf+2);

        var t2 = result["textT"] ? result.textT[nn_daf+2] : "";
        gmaraTextJson = [result.text[nn_daf+2], t1, t2];
        //var t = gmaraTextJson [thisDaf+2];
        
        var dafText = document.getElementById("con-text-gmara");
       // dafText.innerHTML = prossesGmaraText(gmaraTextJson[0], gmaraTextJson[1],gmaraTextJson[2]);
        //console.log(gmaraTextJson);

       
        
    });
*/

 }


 function makeList(n_masechet){

    var len = talmud[n_masechet][1];
    var bar = document.getElementById("bar-daf");
    bar.innerHTML ="";
    for (var i=0; i<len; i++)
    {
     var div = document.createElement("li");
     div.className = "nam-daf";
     div.id = i;
     div.appendChild(document.createTextNode(a(i)));
     div.onclick = function(){
        //var daf = document.getElementById("daf");
        //daf.src = "shas/" + n_masechet + "/" + this.id + ".pdf"
         loadDaf(n_masechet, this.id);
     }
     bar.appendChild(div);

    }
 }


function a(i){
   if(i % 2 == 0 )
   {
    return gimatria(i/2 + 2) + ".";
   }
   else {
    return gimatria(Math.floor(i/2) + 2) + ":";
   }
}

//גימטריה
var letters1 = 'אבגדהוזחטי';
var letters2 = 'יכלמנסעפצק';
var letters3 = 'קרשת';
var letters4 = 'אבגדה';
function gimatria(num) {
    heb = "";
    while (num > 1000) {
        heb += letters4.charAt((num / 1000) - 1);
        heb += "";
        num %= 1000;
    }
    while (num > 400) {
        heb += "ת";
        num -= 400;
    }
    if (num >= 100) {
        heb += letters3.charAt((num / 100) - 1);
        num %= 100;
    }
    if (num >= 10) {
        if (num == 15) {
            heb += 'טו';
            num = 0;
        }
        else if (num == 16) {
            heb += 'טז';
            num = 0;
        }
        else {
            heb += letters2.charAt((num / 10) - 1);
            num %= 10;

        }
    }
    if (num >= 1) {
        heb += letters1.charAt(num - 1);
    }
    if (heb.length > 1) {

        heb = heb.slice(0, heb.length - 1) + heb.charAt(heb.length - 1);
    }
    return heb;
    //document.getElementById("result1").innerHTML = heb;
}

/*
function toggle(id ) {

       var button = document.getElementById("show");
       var masechtot = document.getElementById("masecet-show");

       if(masechtot.style.display == 'none')
          {
            masechtot.style.display = 'block';
            button.innerHTML = "-";
          }
       else
          {
            masechtot.style.display = 'none';
            button.innerHTML = "+";
          }
    }

*/


////mefarshim///



var mefarshimJSON ={};

// thisMasechet =0;
// thisDaf = 0;
function tableMefasim() {
//alert('n');
    mefarshimJSON = {};
    $('#list-mefarshim tr td').empty();
    doobsidian://open?vault=torahNotes&file=%D7%A0%D7%93%D7%A8%D7%99%D7%9D%2F%D7%98%D7%99%D7%95%D7%98%D7%95%D7%AA%2F%D7%94%D7%AA%D7%A4%D7%A1%D7%94%20%D7%91%D7%A0%D7%93%D7%A8%20%D7%95%D7%A9%D7%91%D7%95%D7%A2%D7%94cument.getElementById("con-mefares").innerHTML = "";
    $('.cal-mf').css( "font-weight", "normal" );


    var row = 0;
    var cols = 0;
    var len = Lmefarshim[thisMasechet].length -1;

    for (var i=0; i<len; i++)
     {
        var mefaresh = Lmefarshim[thisMasechet][i+1];

        //console.log("mefarshim/" + mefaresh  + "/" + thisMasechet + ".json");
        $.getJSON("mefarshim/" + mefaresh  + "/" + thisMasechet + ".json", function(result){
            var t = result.text;
            mefarshimJSON[result.id] = t;
            //console.log(mefarshimJSON);
            //console.log(mf[result.id]);
            //console.log(t[thisDaf+2]);

            //prossesMefaresh (t[21]);
            makeDir("cal-mf","mf-" + result.id,mf[result.id],function (event) {
                //click call: 
                     //window.location.assign("masechet.html?no=" + this.id);
                     loadMefaresh(this.id);            
                 },cols,row,"list-mefarshim");
                 cols++;
            if(cols == 5) {row++; cols =0;};

            var tt = mefarshimJSON[result.id][thisDaf+2];
            if (tt === undefined || tt.length === 0  ) {
                //console.log("The string is empty");
                $('#mf-'+ result.id).css( "color", "#E8E8E8" );
            } else {
                    //console.log(t[thisDaf]);
                $('#mf-'+ result.id ).css( "color", "black" );
            }
            
        });
   
     }
     /*
     var slides = document.getElementsByClassName("cal-mf");
     
     for (var i = 0; i < slides.length; i++) {
        console.log(slides);
        var idd = slides.item(i).id.substring(3);
        var tt = mefarshimJSON[idd][thisDaf+2];
        //console.log(slides.item(i));
        if (tt === undefined || tt.length === 0  ) {
            //console.log("The string is empty");
            $(slides.item(i) ).css( "color", "gray" );
        } else {
                //console.log(t[thisDaf]);
                $(slides.item(i) ).css( "color", "black" );
        }
        console.log(slides.item(i).id);
     }
     */
     document.getElementById("title-daf-mefaresh").innerHTML = a(thisDaf);

     //console.log(JSON.stringify(mefarshimJSON));
 
 }
var thisMefaresh = 0;

function loadMefaresh(id){

    var idd = id.substring(3);
    thisMefaresh = idd;
    document.getElementById("con-mefares").innerHTML = "";
    //console.log( a(thisDaf));

    $('.cal-mf').css( "font-weight", "normal" );
    $( "#" + id ).css( "font-weight", "bold" );
    document.getElementById("con-mefares").innerHTML = prossesMefaresh(mefarshimJSON[idd][thisDaf+2]);
    //console.log(prossesMefaresh(mefarshimJSON[idd][thisDaf+2]));

    document.getElementById("title-daf-mefaresh").innerHTML = a(thisDaf);

    var slides = document.getElementsByClassName("cal-mf");
     
     for (var i = 0; i < slides.length; i++) {
       // console.log(slides);
        var idd = slides.item(i).id.substring(3);
        var tt = mefarshimJSON[idd][thisDaf+2];
        //console.log(slides.item(i));
        if (tt === undefined || tt.length === 0  ) {
            //console.log("The string is empty");
            $(slides.item(i) ).css( "color", "#E8E8E8" );
        } else {
                //console.log(t[thisDaf]);
                $(slides.item(i) ).css( "color", "black" );
        }
        //console.log(slides.item(i).id);
     }
    
 }

 function prossesMefaresh(text){
    var t = [];
    t = text;
    var r = "";
    if(Array.isArray(t)){
        t.forEach(function(t1) {
            r += t1 + "<br>" ;
        });
    }
   //console.log(r);
   return r;

 }

//Flatten an array//
 const flatten = (arr) => {
    const result = [];
    arr.forEach((item) => {
      if (Array.isArray(item)) {
        result.push(...flatten(item));
      } else {
        result.push(item);
      }
    });
    return result;
  };


 function prossesGmaraText(text, textR, textT){
    var t = [];
    t = text;
    var r = "";
    r += '<b>גמרא</b><br>';
    
    if (Array.isArray(text)){
        t.forEach(function(t1) {
            r +=  t1 + ".<br>" ;
        });
    }
    //console.log(textR);
    if (Array.isArray(textR)){
        r += '<hr><b>רש״י </b><br>'
        flatten(textR).forEach(function(t2) {
            t2.length>0  ? r += "<b>" + t2.replace("-", "-</b>").replace("–", "-</b>").replace("-", "-</b>") + "<br>" : "";
        });
    }
    if (Array.isArray(textT)){
        r += '<hr><b>תוספות</b><br>'
        flatten(textT).forEach(function(t3) {
            t3.length>0 ? r += "<b>" + t3.replace("-", "-</b>").replace("–", "-</b>").replace("-", "-</b>").replace(".", "-</b>") + "<br>" : "";
        });
    }

 
   return r;

 }

 
function next() {
    if(parseInt(thisDaf) +1 < talmud[thisMasechet][1]){
        loadDaf(thisMasechet, parseInt(thisDaf) +1);
    }

}
function back() {

     if( parseInt(thisDaf) -1 >= 0){
        loadDaf(thisMasechet, parseInt(thisDaf) - 1);
    }
}


 function backMf(){
    back();
    document.getElementById("con-mefares").innerHTML = "";
    !(thisMefaresh == 0) ?  loadMefaresh('mf-' + thisMefaresh) :  document.getElementById("con-mefares").innerHTML = "" ;//prossesMefaresh(mefarshimJSON[thisMefaresh][thisDaf+2]);
    document.getElementById("title-daf-mefaresh").innerHTML = a(thisDaf);


 }
 function nextMf(){
    next()
    document.getElementById("con-mefares").innerHTML = "";
    !(thisMefaresh == 0) ? loadMefaresh('mf-' + thisMefaresh) :  document.getElementById("con-mefares").innerHTML = "";//prossesMefaresh(mefarshimJSON[thisMefaresh][thisDaf+2]);
    document.getElementById("title-daf-mefaresh").innerHTML = a(thisDaf);

 }

 function backG(){
    back();
    //document.getElementById("con-text-gmara").innerHTML = "";
    loadDafText(thisMasechet,thisDaf);
    document.getElementById("title-daf-mefaresh").innerHTML = a(thisDaf);


 }
 function nextG(){
    next()
    //document.getElementById("con-text-gmara").innerHTML = "";
    loadDafText(thisMasechet,thisDaf);
    document.getElementById("title-daf-gmara").innerHTML = a(thisDaf);

 }

 
var myIFrame = document.getElementById("daf-text");
var cssLink = document.createElement("link") 
cssLink.href = "code/css/default.css"; 
cssLink .rel = "stylesheet"; 
cssLink .type = "text/css"; 
//myIFrame.document.body.appendChild(cssLink);
