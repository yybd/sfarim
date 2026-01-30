var curMasecet = {};
var curPerek = 0;
var LengthPrakim = 0;
var ShowBar = true;
var SaveMasecet = 0;
var SavePerek = 0;

$(document).ready(function () {

    //
    if ("SaveMasecetRambam" in localStorage) {
        SaveMasecet = parseInt(localStorage.getItem('SaveMasecetRambam'));
    }
    if ("SavePerekRambam" in localStorage) {
        SavePerek = parseInt(localStorage.getItem('SavePerekRambam'));
        curPerek = SavePerek;
    }

    tableTalmud()
    setMasecet(SaveMasecet, curPerek);

    $("#prev").click(function () {
        if (curPerek - 1 >= 0) {
            setPerek(curPerek - 1);
        }
    });
    $("#next").click(function () {
        if (curPerek + 1 <= LengthPrakim) {
            setPerek(curPerek + 1);
        }
    });
    $("#masechet").click(function () {
        //console.log("ss");
        // $("#shas").toggle();
    });
    $("#toggle").click(function () {
        // $("#shas").toggle();

    });
    $("#bt_copy_nikud").click(function () {
        var v = $("#copy_nikud").val();
        navigator.clipboard.writeText(removeNikud(v));
        $("#copy_nikud").val('');
        console.log(removeNikud(v));
    });
    // if(ShowBar){ $("#shas").show(); } else  $("#shas").hide();


    hideMefaresh();

    // Tab Event Listeners
    $("#tab-rambam").click(function () { console.log('Clicked rambam'); switchTab('rambam'); });
    $("#tab-mm").click(function () { console.log('Clicked mm'); switchTab('mm'); });
    $("#tab-km").click(function () { console.log('Clicked km'); switchTab('km'); });


})

function hideMefaresh() {
    if ($("#mm").text().trim().length === 0) {
        console.log("mm is empty");
        $(".mefaresh-mm").hide();
    } else {
        $(".mefaresh-mm").show();
    }

    if ($("#km").text().trim().length === 0) {
        $(".mefaresh-km").hide();
        console.log("km is empty");
    } else {
        $(".mefaresh-km").show();
    }
}


function setMasecet(n, p) {

    curMasecet = eval(talmud[n][1]);
    LengthPrakim = eval(curMasecet).text.length - 1;
    //console.log(curMasecet);
    setPerek(p);
    listPrakim();
    localStorage.setItem('SaveMasecetRambam', n);


}


function getPerek(data, n, rabad = false) {
    const para = document.createElement("p");
    //console.log(curMasecet.text[n]);
    // if (typeof data[n] !== 'undefined' && data[n] !== null) {
    try {
        var p = data[n];

        for (let i = 0; i < p.length; i++) {
            const herf = document.createElement("a");
            const span = document.createElement("span");
            var txt = p[i];
            if (rabad) {
                txt = removeNikud(p[i]);
            }
            herf.innerHTML = (p[i]).length > 0 ? "<span class='halacha'> " + gimatria(i + 1) + "&nbsp&nbsp</span>" : "";
            span.innerHTML = p[i] ? "<span class='perek'> " + txt + "</span>" : "";
            para.appendChild(herf);
            para.appendChild(span);

            if (rabad) {
                try {
                    var rabadt = curMasecet.textrabad[n];
                    const spanRabad = document.createElement("span");
                    spanRabad.innerHTML = rabadt[i] ? "<span class='rabad'> " + rabadt[i] + "</span>" : "";
                    para.appendChild(spanRabad);
                } catch (e) {
                    console.error("Error processing Rabad for perek " + n + ", halacha " + (i + 1) + ": " + e);
                }
            }

        }
    } catch (e) {
        console.error("Error processing data for perek " + n + ": " + e);
    }

    //}
    //const node = document.createHtmlNode(copyItems);
    //para.appendChild(node);
    //para.innerHTML = copyItems
    return para;
}

function setPerek(n) {

    const elerambam = document.getElementById("rambam");
    const elemm = document.getElementById("mm");
    const elekm = document.getElementById("km");
    $("#rambam").empty();
    $("#mm").empty();
    $("#km").empty();

    elerambam.appendChild(getPerek(curMasecet.text, n, true));
    elemm.appendChild(getPerek(curMasecet.textmm, n));
    elekm.appendChild(getPerek(curMasecet.textkm, n));
    //var title = eval(curMasecet).heTitle + " פרק " + gimatria(n + 1);
    $("#name-rambam").text(eval(curMasecet).heTitle);
    $("#rambam-title").text(" פרק " + gimatria(n + 1));
    document.title = eval(curMasecet).heTitle + " פרק " + gimatria(n + 1);

    curPerek = n;
    localStorage.setItem('SavePerekRambam', n);

    if (curPerek == 0) {
        $(".bi-chevron-right").hide();
    } else { $(".bi-chevron-right").show(); };

    if (curPerek == LengthPrakim) {
        $(".bi-chevron-left").hide();
    } else { $(".bi-chevron-left").show(); };

    hideMefaresh();


    window.scrollTo({ top: 0, behavior: 'smooth' });

}

function switchTab(tabName) {
    console.log('Switching to tab:', tabName);
    try {
        // Remove active class from all tabs
        var tabs = document.querySelectorAll('#mobile-tabs .col');
        if (tabs) {
            tabs.forEach(function (el) { el.classList.remove('active-tab'); });
        }

        // Add active class to clicked tab
        var activeTab = document.getElementById('tab-' + tabName);
        if (activeTab) activeTab.classList.add('active-tab');

        var columns = ['rambam', 'mm', 'km'];
        columns.forEach(function (col) {
            var els = document.querySelectorAll('.mobile-col-' + col);
            if (col === tabName) {
                els.forEach(function (el) {
                    el.classList.remove('mobile-d-none');
                    el.classList.add('mobile-d-block');
                    // Remove d-none if present (Bootstrap class)
                    el.classList.remove('d-none');
                });
            } else {
                els.forEach(function (el) {
                    el.classList.remove('mobile-d-block');
                    el.classList.add('mobile-d-none');
                });
            }
        });
    } catch (e) {
        console.error('Error in switchTab:', e);
    }
}

function listPrakim() {
    const elelist = document.getElementById("list");
    $("#list").empty();
    for (let i = 0; i < LengthPrakim + 1; i++) {
        const li = document.createElement("li");
        li.className = 'list-item';
        li.innerHTML = gimatria(i + 1);
        li.onclick = function () {
            setPerek(i)
        }
        elelist.appendChild(li);
    }


}


function tableTalmud() {

    var row = 0;
    var cols = 0;
    var len = talmud.length;
    for (var i = 0; i < len; i++) {
        makeDir("cal", i, talmud[i][0], function () {
            //window.location.assign("masechet.html?no=" + this.id);
            //showDivDaf(this.id);
            //console.log(talmud[this.id][1]);
            setMasecet(this.id, 0);


            // $("#shas").toggle();

        }, cols, row, "list-rambam-id")

        cols++;
        if (cols == 5) { row++; cols = 0; }
    }


}

function makeDir(name, id, conect, click, column, row, tableID) {

    var div = document.createElement("div");
    div.className = name;
    div.id = id;
    div.setAttribute("data-bs-dismiss", "modal");
    div.appendChild(document.createTextNode(conect));
    div.onclick = click;

    if (talmud[id][2]) { div.style.fontWeight = "bold"; }

    var tbl = document.getElementById(tableID);
    if (tbl) { tbl.rows[row].cells[column].appendChild(div); }

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

function removeNikud(t) {
    var r = t.replace(/\u05BE/g, "-").replace(/[\u05B0-\u05C7]/g, "");
    return r;
}


var talmud = [
    ["יסודי התורה", "Foundations_of_the_Torah", 1],
    ["דעות", "Human_Dispositions", 1],
    ["תלמוד תורה", "Torah_Study", 1],
    ["עבודה זרה", "Foreign_Worship_and_Customs_of_the_Nations", 1],
    ["תשובה", "Repentance", 1],

    ["קריאת שמע", "Reading_the_Shema", 0],
    ["תפילה וברכת כהנים", "Prayer_and_the_Priestly_Blessing", 0],
    ["תפילין מזוזה וס״ת", "Tefillin_Mezuzah_and_the_Torah_Scroll", 0],
    ["ציצית", "Fringes", 0],
    ["ברכות", "Blessings", 0],
    ["מילה", "Circumcision", 0],
    ["סדר התפילה", "The_Order_of_Prayer", 0],


    ["שבת", "Sabbath", 1],
    ["עירובין", "Eruvin", 1],
    ["שביתת העשור", "Rest_on_the_Tenth_of_Tishrei", 1],
    ["יום טוב", "Rest_on_a_Holiday", 1],
    ["חמץ ומצה", "Leavened_and_Unleavened_Bread", 1],
    ["שופר סוכה ולולב", "Shofar_Sukkah_and_Lulav", 1],
    ["שקלים", "Sheqel_Dues", 1],
    ["קידוש החודש", "Sanctification_of_the_New_Month", 1],
    ["תעניות", "Fasts", 1],
    ["מגילה וחנוכה", "Scroll_of_Esther_and_Hanukkah", 1],

    ["אישות", "Marriage", 0],
    ["גירושין", "Divorce", 0],
    ["יבום וחליצה", "Levirate_Marriage_and_Release", 0],
    ["נערה בתולה", "Virgin_Maiden", 0],
    ["סוטה", "Woman_Suspected_of_Infidelity", 0],

    ["איסורי ביאה", "Forbidden_Intercourse", 1],
    ["מאכלות אסורות", "Forbidden_Foods", 1],
    ["שחיטה", "Ritual_Slaughter", 1],

    ["שבועות", "Oaths", 0],
    ["נדרים", "Vows", 0],
    ["נזירות", "Nazariteship", 0],
    ["ערכים וחרמים", "Appraisals_and_Devoted_Property", 0],

    ["כלאים", "Diverse_Species", 1],
    ["מתנות עניים", "Gifts_to_the_Poor", 1],
    ["תרומות", "Heave_Offerings", 1],
    ["מעשרות", "Tithes", 1],
    ["מעשר שני ונטע רבעי", "Second_Tithes_and_Fourth_Year_s_Fruit", 1],
    ["ביכורים", "First_Fruits_and_other_Gifts_to_Priests_Outside_the_Sanctuary", 1],
    ["שמיטה ויובל", "Sabbatical_Year_and_the_Jubilee", 1],

    ["בית הבחירה", "The_Chosen_Temple", 0],
    ["כלי המקדש", "Vessels_of_the_Sanctuary_and_Those_who_Serve_Therein", 0],
    ["ביאת מקדש", "Admission_into_the_Sanctuary", 0],
    ["איסורי מזבח", "Things_Forbidden_on_the_Altar", 0],
    ["מעשה הקרבנות", "Sacrificial_Procedure", 0],
    ["תמידין ומוספין", "Daily_Offerings_and_Additional_Offerings", 0],
    ["פסולי המוקדשין", "Sacrifices_Rendered_Unfit", 0],
    ["עבודת יוה״כ", "Service_on_the_Day_of_Atonement", 0],
    ["מעילה", "Trespass", 0],

    ["קרבן פסח", "Paschal_Offering", 1],
    ["חגיגה", "Festival_Offering", 1],
    ["בכורות", "Firstlings", 1],
    ["שגגות", "Offerings_for_Unintentional_Transgressions", 1],
    ["מחוסרי כפרה", "Offerings_for_Those_with_Incomplete_Atonement", 1],
    ["תמורה", "Substitution", 1],

    ["טומאת מת", "Defilement_by_a_Corpse", 0],
    ["פרה אדומה", "Red_Heifer", 0],
    ["טומאת צרעת", "Defilement_by_Leprosy", 0],
    ["מטמאי משכב ומושב", "Those_Who_Defile_Bed_or_Seat", 0],
    ["שאר אבות הטומאות", "Other_Sources_of_Defilement", 0],
    ["טומאת אוכלין", "Defilement_of_Foods", 0],
    ["כלים", "Vessels", 0],
    ["מקוואות", "Immersion_Pools", 0],


    ["נזקי ממון", "Damages_to_Property", 1],
    ["גניבה", "Theft", 1],
    ["גזילה ואבידה", "Robbery_and_Lost_Property", 1],
    ["חובל ומזיק", "One_Who_Injures_a_Person_or_Property", 1],
    ["רוצח ושמירת נפש", "Murderer_and_the_Preservation_of_Life", 1],

    ["מכירה", "Sales", 0],
    ["זכיה ומתנה", "Ownerless_Property_and_Gifts", 0],
    ["שכנים", "Neighbors", 0],
    ["שלוחין ושותפין", "Agents_and_Partners", 0],
    ["עבדים", "Slaves", 0],

    ["שכירות", "Hiring", 1],
    ["שאלה ופקדון", "Borrowing_and_Deposit", 1],
    ["מלוה ולוה", "Creditor_and_Debtor", 1],
    ["טוען ונטען", "Plaintiff_and_Defendant", 1],
    ["נחלות", "Inheritances", 1],

    ["סנהדרין", "The_Sanhedrin_and_the_Penalties_within_their_Jurisdiction", 0],
    ["עדות", "Testimony", 0],
    ["ממרים", "Rebels", 0],
    ["אבל", "Mourning", 0],
    ["מלכים ומלחמות", "Kings_and_Wars", 0]
];


