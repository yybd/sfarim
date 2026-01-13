var curSefer = {};
var curPerek = 0;
var LengthPrakim = 0;
var ShowBar = true;
var SaveSefer = 0;
var SavePerek = 0;
var font = "TaameyFrank";
var teamim = 0;

$(document).ready(function () {

//
        if ("SaveSeferTanach" in localStorage) {
            SaveSefer= parseInt(localStorage.getItem('SaveSeferTanach'));
        }
        if ("SavePerekTanach" in localStorage) {
            SavePerek= parseInt(localStorage.getItem('SavePerekTanach'));
            curPerek = SavePerek;
        }
        if ("font" in localStorage) {
            font= localStorage.getItem('font');
        }
        else {localStorage.setItem('teamim', teamim);}
        if ("teamim" in localStorage) {
            teamim= parseInt(localStorage.getItem('teamim'));
        }
        else {localStorage.setItem('teamim', teamim.toString());}

        loadFont(localStorage.getItem('font'), teamim ? "TaameyFrank": "ShlomoSemiStam");

        tableTanach() 
        setSefer(SaveSefer, curPerek);
             
       $("#prev").click(function(){
            if(curPerek -1 >= 0){
                setPerek(curPerek -1);
            }
        }); 
       $("#next").click(function(){
            if(curPerek +1 <= LengthPrakim){
                setPerek(curPerek +1);
            }
        }); 
        $("#font").click(function(){
            console.log("ff");
            if( localStorage.getItem('font') == "TaameyFrank"){
                localStorage.setItem('font', "ShlomoSemiStam");
                localStorage.setItem('teamim', "1");
            }
            else {localStorage.setItem('font', "TaameyFrank")
                localStorage.setItem('teamim', "0");
            }
           loadFont(font);
           location.reload()


        }); 
        $("#masechet").click(function(){
            //console.log("ss");
           // $("#shas").toggle();
        }); 
        $("#toggle").click(function(){
           // $("#shas").toggle();

        }); 
        $("#bt_copy_nikud").click(function () {
            var v = $("#copy_nikud").val();
            navigator.clipboard.writeText(removeNikud(v));
            $("#copy_nikud").val('');
            console.log(removeNikud(v));
        });
       // if(ShowBar){ $("#shas").show(); } else  $("#shas").hide();
        
 
})


function setSefer(n,p){

    curSefer = eval(tanach[n][1]);
    LengthPrakim = eval(curSefer).text.length - 1;
    setPerek(p);
    listPrakim();
    localStorage.setItem('SaveSeferTanach', n);


}


function getPerek(data, n){
    const para = document.createElement("p");
    var p = data[n];
    var pp = "";
    for (let i = 0; i < p.length; i++) {
        const herf = document.createElement("a");
        const span = document.createElement("span");

        herf.innerHTML  = "<span class='pasuk'> " + gimatria(i + 1) + "&nbsp&nbsp</span>";
        //console.log(gimatria(i + 1))
        var text = "";
        if(!teamim){text= rTeamim( p[i])} else text =  p[i];
        span.innerHTML = text;
        para.appendChild(herf);
        para.appendChild(span);
        //copyItems += pe;
      }
    //const node = document.createHtmlNode(copyItems);
    //para.appendChild(node);
    //para.innerHTML = copyItems
    //console.log(para);
    return para;
}

function setPerek(n){
    
    const eletanach = document.getElementById("tanach-con");
    //const elebartenura = document.getElementById("bartenura");
    //const elerambam = document.getElementById("rambam");
    $("#tanach-con").empty();
    //$("#bartenura").empty();
    //$("#rambam").empty();
    //console.log(curSefer.text[n].toString())
    eletanach.appendChild(getPerek(curSefer.text,n));
    //elebartenura.appendChild(getPerek(curSefer.text,n));
    //elerambam.appendChild(getPerek(curSefer.textrambam,n));
    //var title = eval(curSefer).heTitle + " פרק " + gimatria(n + 1);
    $("#name-tanach").text(eval(curSefer).heTitle);
    $("#tanach-title").text(" פרק " + gimatria(n + 1));
    document.title = eval(curSefer).heTitle + " פרק " + gimatria(n + 1);

    curPerek = n ;
    localStorage.setItem('SavePerekTanach', n);

    if (curPerek == 0) {
        $(".bi-chevron-right").hide();
    }else {$(".bi-chevron-right").show();};
    
    if (curPerek == LengthPrakim) {
        $(".bi-chevron-left").hide();
    }else {$(".bi-chevron-left").show();};

    window.scrollTo({ top: 0, behavior: 'smooth' });

}

function listPrakim(){
    const elelist = document.getElementById("list");
    $("#list").empty();
    for (let i = 0; i < LengthPrakim + 1; i++) {
        const li = document.createElement("li");
        li.className = 'list-item';
        li.innerHTML = gimatria(i + 1);
        li.onclick = function(){
            setPerek(i)
        }
        elelist.appendChild(li);
    }
    

}


function tableTanach() {
   
    var row = 0;
    var cols = 0;
    var len = tanach.length;
    for (var i=0; i<len; i++)
     {
       makeDir("cal",i,tanach[i][0],function () {
             //window.location.assign("masechet.html?no=" + this.id);
             //showDivDaf(this.id);
             //console.log(tanach[this.id][1]);
             //setSefer(sefer,perek);
             setSefer(this.id,0);
             

            // $("#shas").toggle();

         },cols,row,"tanach")
         
       cols++;
       if(cols == 5) {row++; cols =0;}
     }
    
    
 }
 
 function makeDir(name, id, conect,click, column, row, tableID) {
 
      var div = document.createElement("div");
      div.className = name;
      div.id = id;
      div.setAttribute("data-bs-dismiss", "modal");
      div.appendChild(document.createTextNode(conect));
      div.onclick = click;

      if(tanach[id][2]){div.style.fontWeight = "bold"; }
      
      var tbl = document.getElementById(tableID);
      if(tbl) {tbl.rows[row].cells[column].appendChild(div);}
 
      return div;
  }

  //font change
function loadFont(name1,name2){
    const eletanach = document.getElementById("tanach-con");
    eletanach.style.fontFamily = name1;

    const elefont = document.getElementById("font-button");
    elefont.style.fontFamily = name2;


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

function removeNikud(t){
    var r = t.replace(/\u05BE/g," ").replace(/[\u05B0-\u05C7]/g,"");
    //remove teamin
    var rr = r.replace(/\u05BE/g," ").replace(/[\u0591-\u05AF]/g,"");
     // var r = t.normalize('NFD').replace(/[\u0300-\u036f]/g, '');

    return rr;
}
//remove teamim
function rTeamim(t){
        var rr = t.replace(/\u05BE/g," ").replace(/[\u0591-\u05AF]/g,"");
            return rr;
}


var tanach = [
    ["בראשית", "Genesis",1],
    ["שמות", "Exodus",1],
    ["ויקרא","Leviticus",1],
    ["במדבר","Numbers",1],
    ["דברים","Deuteronomy",1],

    ["יהושע","Joshua",0],
    ["שופטים","Judges",0],
    ["שמואל א","I_Samuel",0],
    ["שמואל ב","II_Samuel",0],
    ["מלכים א","I_Kings",0],
    ["מלכים ב","II_Kings",0],
    ["ישעיהו", "Isaiah",0],
    ["ירמיהו","Jeremiah",0],
    ["יחזקאל","Ezekiel",0],
    ["הושע","Hosea",0],
    ["יואל","Joel",0],
    ["עמוס","Amos",0],
    ["עובדיה","Obadiah",0],
    ["יונה","Jonah",0],
    ["מיכה","Micah",0],
    ["נחום","Nahum",0],
    ["חבקוק","Habakkuk",0],
    ["צפניה","Zephaniah",0],    
    ["חגי","Haggai",0],
    ["זכריה","Zechariah",0],
    ["מלאכי","Malachi",0],

    ["דברי הימים א","I_Chronicles",1],
    ["דברי הימים ב","II_Chronicles",1],
    ["תהילים","Psalms",1],
    ["איוב","Job",1],  
    ["משלי","Proverbs",1],
    ["רות","Ruth",1],
    ["שיר השירים","Song_of_Songs",1],
    ["קהלת","Ecclesiastes",1],
    ["איכה","Lamentations",1],
    ["אסתר","Esther",1],
    ["דניאל","Daniel",1],
    ["עזרא","Ezra",1],
    ["נחמיה","Nehemiah",1]];


