var curMasecet = {};
var curPerek = 0;
var LengthPrakim = 0;
var ShowBar = true;
var SaveMasecet = 0;
var SavePerek = 0;

$(document).ready(function () {

//
        if ("SaveMasecetMishna" in localStorage) {
            SaveMasecet= parseInt(localStorage.getItem('SaveMasecetMishna'));
        }
        if ("SavePerekMishna" in localStorage) {
            SavePerek= parseInt(localStorage.getItem('SavePerekMishna'));
            curPerek = SavePerek;
        }

        tableTalmud() 
        setMasecet(SaveMasecet, curPerek);
             
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


function setMasecet(n,p){

    curMasecet = eval(talmud[n][1] + "json");
    LengthPrakim = eval(curMasecet).textmishna.length - 1;
    setPerek(p);
    listPrakim();
    localStorage.setItem('SaveMasecetMishna', n);


}


function getPerek(data, n){
    const para = document.createElement("p");
    var p = data[n];
    for (let i = 0; i < p.length; i++) {
        const herf = document.createElement("a");
        const span = document.createElement("span");

        herf.innerHTML  = "" + gimatria(i + 1) + "&nbsp&nbsp";
        //console.log(gimatria(i + 1))
        span.innerHTML = p[i];
        para.appendChild(herf);
        para.appendChild(span);
        //copyItems += pe;
      }
    //const node = document.createHtmlNode(copyItems);
    //para.appendChild(node);
    //para.innerHTML = copyItems
    return para;
}

function setPerek(n){
    
    const elemishna = document.getElementById("mishna");
    const elebartenura = document.getElementById("bartenura");
    const elerambam = document.getElementById("rambam");
    $("#mishna").empty();
    $("#bartenura").empty();
    $("#rambam").empty();
    
    elemishna.appendChild(getPerek(curMasecet.textmishna,n));
    elebartenura.appendChild(getPerek(curMasecet.textbartenura,n));
    elerambam.appendChild(getPerek(curMasecet.textrambam,n));
    //var title = eval(curMasecet).heTitle + " פרק " + gimatria(n + 1);
    $("#name-mishna").text(eval(curMasecet).heTitle);
    $("#mishna-title").text(" פרק " + gimatria(n + 1));
    document.title = eval(curMasecet).heTitle + " פרק " + gimatria(n + 1);

    curPerek = n ;
    localStorage.setItem('SavePerekMishna', n);

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


function tableTalmud() {
   
    var row = 0;
    var cols = 0;
    var len = talmud.length;
    for (var i=0; i<len; i++)
     {
       makeDir("cal",i,talmud[i][0],function () {
             //window.location.assign("masechet.html?no=" + this.id);
             //showDivDaf(this.id);
             //console.log(talmud[this.id][1]);
             setMasecet(this.id,0);
             

            // $("#shas").toggle();

         },cols,row,"shas")
         
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

      if(talmud[id][2]){div.style.fontWeight = "bold"; }
      
      var tbl = document.getElementById(tableID);
      if(tbl) {tbl.rows[row].cells[column].appendChild(div);}
 
      return div;
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
    var r = t.replace(/\u05BE/g,"-").replace(/[\u05B0-\u05C7]/g,"");
    return r;
}


var talmud = [
    ["ברכות", "Berakhot",1],
    ["פאה", "Peah",1],
    ["דמאי","Demai",1],
    ["כלאים","Kilayim",1],
    ["שביעית","Sheviit",1],
    ["תרומות","Terumot",1],
    ["מעשרות","Maasrot",1],
    ["מעשר שני","MaaserSheni",1],
    ["חלה","Challah",1],
    ["ערלה","Orlah",1],
    ["ביכורים","Bikkurim",1],

    ["שבת", "Shabbat",0],
    ["עירובין","Eruvin",0],
    ["פסחים","Pesachim",0],
    ["שקלים","Shekalim",0],
    ["ראש השנה","RoshHashanah",0],
    ["יומא","Yoma",0],
    ["סוכה","Sukkah",0],
    ["ביצה","Beitzah",0],
    ["תענית","Taanit",0],
    ["מגילה","Megillah",0],
    ["מועד קטן","MoedKatan",0],
    ["חגיגה","Chagigah",0],
    
    ["יבמות","Yevamot",1],
    ["כתובות","Ketubot",1],
    ["נדרים","Nedarim",1],
    ["נזיר","Nazir",1],
    ["סוטה","Sotah",1],
    ["גיטין","Gittin",1],
    ["קידושין","Kiddushin",1],
    
    ["בבא קמא","BabaKama",0],
    ["בבא מציעא","BabaMetzia",0],
    ["בבא בתרא","BabaBatra",0],
    ["סנהדרין","Sanhedrin",0],
    ["מכות","Makkot",0],
    ["שבועות","Shevuot",0],
    ["עדיות","Eduyot",0],
    ["עבודה זרה","AvodahZarah",0],
    ["אבות","Avot",0],
    ["הוריות","Horayot",0],
    
    ["זבחים","Zevachim",1],
    ["מנחות","Menachot",1],
    ["חולין","Chullin",1],
    ["בכורות","Bekhorot",1],
    ["ערכין","Arakhin",1],
    ["תמורה","Temurah",1],
    ["כריתות","Keritot",1],
    ["מעילה","Meilah",1],
    ["קינין","Kinnim",1],
    ["תמיד","Tamid",1],
    ["מדות","Middot",1],
    
    ["כלים","Kelim",0],
    ["אהלות","Oholot",0],
    ["נגעים","Negaim",0],
    ["פרה","Parah",0],
    ["טהרות","Tahorot",0],
    ["מקוואות","Mikvaot",0],
    ["נדה","Niddah",0],
    ["מכשירין","Makhshirin",0],
    ["זבין","Zavim",0],
    ["טבול יום","TevulYom",0],
    ["ידים","Yadayim",0],
    ["עוקצין","Oktzin",0]];


