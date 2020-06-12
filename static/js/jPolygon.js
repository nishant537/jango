// This file handles interative region selection functionality

var perimeter = new Array();
var complete = false;
var numberOfCanvasses = 4;
var canvasList = [];
for(var i=1; i<=numberOfCanvasses; i++){
    var id = "jPolygon".concat(i.toString());
    var canvas = document.getElementById(id);
    canvasList[i] = canvas
}
var ctx;

//function line_intersects(p0, p1, p2, p3) {
//
//    var s1_x, s1_y, s2_x, s2_y;
//    s1_x = p1['x'] - p0['x'];
//    s1_y = p1['y'] - p0['y'];
//    s2_x = p3['x'] - p2['x'];
//    s2_y = p3['y'] - p2['y'];
//
//    var slope_1, slope_2
//    slope_1 = s1_y/s1_x
//    slope_2 = s2_y/s2_x
//
//    result_point_1
//    var s, t;
//    s = (-s1_y * (p0['x'] - p2['x']) + s1_x * (p0['y'] - p2['y'])) / (-s2_x * s1_y + s1_x * s2_y);
//    t = ( s2_x * (p0['y'] - p2['y']) - s2_y * (p0['x'] - p2['x'])) / (-s2_x * s1_y + s1_x * s2_y);
//
//    if (s >= 0 && s <= 1 && t >= 0 && t <= 1)
//    {
//        // Collision detected
//        return true;
//    }
//    return false; // No collision
//}

function line_intersects(p0, p1, p2, p3) {
  var a,b,c,d,p,q,r,s;
  a = p0['x']
  b = p0['y']
  c = p1['x']
  d = p1['y']
  p = p2['x']
  q = p2['y']
  r = p3['x']
  s = p3['y']
  var det, gamma, lambda;
  det = (c - a) * (s - q) - (r - p) * (d - b);
  if (det === 0) {
    return false;
  } else {
    lambda = ((s - q) * (r - a) + (p - r) * (s - b)) / det;
    gamma = ((b - d) * (r - a) + (c - a) * (s - b)) / det;
    return (0 < lambda && lambda < 1) && (0 < gamma && gamma < 1);
  }
}

function point(x, y){
    ctx.fillStyle="white";
    ctx.strokeStyle = "white";
    ctx.fillRect(x-2,y-2,4,4);
    ctx.moveTo(x,y);
}

function undo(){
    ctx = undefined;
    perimeter.pop();
    complete = false;
    start(true);
}

function clear_canvas(region_num){
    ctx = undefined;
    perimeter = new Array();
    complete = false;
    if (region_num == '0'){
        for (var i=1; i<4; i++){
            var coordinates_generic = 'coordinates';
            var element_id = coordinates_generic.concat(i.toString());
            document.getElementById(element_id).value = '';
        }
    }
    else{
        var coordinates_generic = 'coordinates';
        var element_id = coordinates_generic.concat(region_num);
        document.getElementById(element_id).value = '';
    }

    start(false, region_num);
}

function reformatAndResize(perimeter){
    var finalString = '';
    var arrayLength = perimeter.length;
    for (var i = 0; i < arrayLength; i++) {
        var temp = perimeter[i]['x'].toString();
        finalString = finalString.concat(temp);
        finalString = finalString.concat(',');
        finalString = finalString.concat(perimeter[i]['y'].toString());
        if (i != arrayLength - 1){
            finalString = finalString.concat(';');
        }
    }
    return finalString;
}

function draw(end, region_num){
    ctx.lineWidth = 1;
    ctx.strokeStyle = "white";
    ctx.lineCap = "square";
    ctx.beginPath();
    var coordinates_generic = 'coordinates';
    var element_id = coordinates_generic.concat(region_num.toString());
    for(var i=0; i<perimeter.length; i++){
        if(i==0){
            ctx.moveTo(perimeter[i]['x'],perimeter[i]['y']);
            end || point(perimeter[i]['x'],perimeter[i]['y']);
        } else {
            ctx.lineTo(perimeter[i]['x'],perimeter[i]['y']);
            end || point(perimeter[i]['x'],perimeter[i]['y']);
        }
    }
    if(end){
        ctx.lineTo(perimeter[0]['x'],perimeter[0]['y']);
        ctx.closePath();
        ctx.fillStyle = 'rgba(255, 0, 0, 0.5)';
        ctx.fill();
        ctx.strokeStyle = 'blue';
        complete = true;
    }
    ctx.stroke();

    // print coordinates
    if(perimeter.length == 0){
        document.getElementById(element_id).value = '';
    } else {
        modPerimeter = reformatAndResize(perimeter);
        if (complete){
            document.getElementById(element_id).value = (modPerimeter);
        }
    }
}

function check_intersect(x,y){
    if(perimeter.length < 3){
        return false;
    }
    var p0 = new Array();
    var p1 = new Array();
    var p2 = new Array();
    var p3 = new Array();

    p2['x'] = perimeter[perimeter.length-1]['x'];
    p2['y'] = perimeter[perimeter.length-1]['y'];
    p3['x'] = x;
    p3['y'] = y;

    for(var i=0; i<perimeter.length-1; i++){
        p0['x'] = perimeter[i]['x'];
        p0['y'] = perimeter[i]['y'];
        p1['x'] = perimeter[i+1]['x'];
        p1['y'] = perimeter[i+1]['y'];
        if(p1['x'] == p2['x'] && p1['y'] == p2['y']){ continue; }
        if(p0['x'] == p3['x'] && p0['y'] == p3['y']){ continue; }
        if(line_intersects(p0,p1,p2,p3)==true){
            return true;
        }
    }
    return false;
}

function point_it(event, region_num) {
    if(complete){
        alert('Polygon already created');
        return false;
    }
    var rect, x, y;

    if(event.ctrlKey || event.which === 3 || event.button === 2){
        if(perimeter.length==2){
            alert('You need at least three points for a polygon');
            return false;
        }
        x = perimeter[0]['x'];
        y = perimeter[0]['y'];
        if(check_intersect(x,y)){
            alert('The line you are drawing intersects another line');
            return false;
        }
        draw(true, region_num);
        alert('Polygon closed');
	    event.preventDefault();
        return false;
    } else {
        rect = canvasList[region_num].getBoundingClientRect();
        x = event.clientX - rect.left;
        y = event.clientY - rect.top;
        if (perimeter.length>0 && x == perimeter[perimeter.length-1]['x'] && y == perimeter[perimeter.length-1]['y']){
            // same point - double click
            return false;
        }
        if(check_intersect(x,y)){
            alert('The line you are drawing intersects another line');
            return false;
        }
        perimeter.push({'x':x,'y':y});
        draw(false, region_num);
        return false;
    }
}

function start(with_draw, region_num) {
    var img = new Image();
    if (region_num == 0){
        region_num = 1;
    }
    img.src = canvasList[region_num].getAttribute('data-imgsrc');
    img.onload = function(){
        ctx = canvasList[region_num].getContext("2d");
        ctx.drawImage(img, 0, 0, canvasList[region_num].width, canvasList[region_num].height);
        if(with_draw == true){
            draw(false, region_num);
        }
    }
}
