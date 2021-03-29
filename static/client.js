// index.js for pilot annotation

// --------------------------
// utility
// --------------------------

// escape for jQuery selector
String.prototype.escape_selector = function() {
  return this.replace(/[ !"#$%&'()*+,.\/:;<=>?@\[\\\]^`{|}~]/g, "\\$&");
}

// convert UTF-8 string to hex string
String.prototype.hex_encode = function() {
  let arr = Array.from((new TextEncoder('utf-8')).encode(this)).map(
    v => v.toString(16));
  return arr.join('');
}

// construct the idf dict from a mi element
function get_idf(elem) {
  let idf = {};
  idf.hex = elem.text().hex_encode();
  idf.var = 'default';

  let var_cand = elem.attr('mathvariant');
  if(var_cand != undefined) {
    if(var_cand == 'normal') {
      idf.var = 'roman';
    } else {
      idf.var = var_cand;
    }
  }

  let concept_cand = elem.data('math-concept');
  if(concept_cand != undefined) {
    idf.concept = Number(concept_cand);
  } else {
    idf.concept = undefined;
  }

  return idf;
}

// --------------------------
// prepare the mcdict table
// --------------------------

// load from the external json file
let mcdict = {};
$.ajax({
  url: '/mcdict.json',
  dataType: 'json',
  async: false,
  success: function(data) {
    mcdict = data;
  }
});

// define color for each concept
let colors = [
  '#008b8b', '#ff7f50', '#ff4500', '#2f4f4f', '#006400', '#dc143c',
  '#c71585', '#4169e1', '#2e8b57', '#ff1493', '#191970', '#ff69b4',
  '#ff69b4', '#0000cd', '#f4a460', '#ff00ff', '#7cfc00', '#d2691e',
  '#a0522d', '#800000', '#9400d3', '#556b2f', '#4b0082', '#808000'
];

let cnt = 0;
for(let idf_hex in mcdict) {
  for(let idf_var in mcdict[idf_hex]) {
    for(let concept in mcdict[idf_hex][idf_var]) {
      if(mcdict[idf_hex][idf_var][concept].description != undefined) {
        mcdict[idf_hex][idf_var][concept].color = colors[cnt % colors.length];
        cnt++;
      }
    }
  }
}

// accessors
function get_concept(idf) {
  if(mcdict[idf.hex] != undefined &&
    mcdict[idf.hex][idf.var] != undefined &&
    mcdict[idf.hex][idf.var][idf.concept] != undefined &&
    mcdict[idf.hex][idf.var][idf.concept].description != undefined)
    return mcdict[idf.hex][idf.var][idf.concept];
  else
    return undefined;
}

function get_concept_cand(idf) {
  if(mcdict[idf.hex] != undefined)
    return mcdict[idf.hex][idf.var]; // can be undefined
}

// --------------------------
// mathcolor
// --------------------------

function give_color(target) {
  let idf = get_idf(target);
  let concept = get_concept(idf);
  if(concept != undefined) {
    target.attr('mathcolor', concept.color);
  }
}

$(function() {
  $('mi').each(function() {
    give_color($(this));
  })
})

// --------------------------
// SoG highlight
// --------------------------

// load sog from the external json file
let sog = {};
$.ajax({
  url: '/sog.json',
  dataType: 'json',
  async: false,
  success: function(data) {
    sog = data;
  }
});

$(function() {
  for(let s of sog.sog) {
    // get SoG nodes
    // Note: this code is somehow very tricky but it works
    let sog_nodes;
    if (s.start_id == s.stop_id) {
      sog_nodes = $('#' + s.start_id.escape_selector());
    } else {
      let start_node = $('#' + s.start_id.escape_selector());
      let stop_node = $('#' + s.stop_id.escape_selector());

      sog_nodes = start_node.nextUntil('#' + s.stop_id.escape_selector()).addBack().add(stop_node);
    }

    // get the concept for the SoG
    let idf = get_idf($('#' + s.mi_id.escape_selector()));
    let concept = get_concept(idf);

    // highlight it!
    sog_nodes.css('background-color', concept.color);
    sog_nodes.attr({
      'data-sog-mi': s.mi_id,
      'data-sog-start': s.start_id,
      'data-sog-stop': s.stop_id,
    })
  }
})

// --------------------------
// tooltip
// --------------------------

$(function() {
  $(document).tooltip({
    show: false,
    hide: false,
    items: '[data-math-concept]',
    content: function() {
      let idf = get_idf($(this));
      return get_concept(idf).description;
    },
    open: function(event, ui) {
      $('mi').each(function() {
        give_color($(this));
      })
    }
  });
});

// --------------------------
// Annotation box
// --------------------------

$(function() {
  // show the box for annotation in the sidebar 
  function draw_anno_box(mi_id, idf, concept_cand) {
    // box title
    let title = '<div class="sidebar-box-title">' + mi_id + '</div>'

    // construct the form with the candidate list
    let hidden = `<input type="hidden" name="mi_id" value="${mi_id}" />`;
    let radios = '';

    for(let concept_id in concept_cand) {
      let concept = concept_cand[concept_id];

      let check = (concept_id == idf.concept) ? 'checked' : '';
      let input = `<input type="radio" name="concept" value="${concept_id}" ${check} />`;

      let args_info = 'NONE';
      if(concept.args_type.length > 0) {
        args_info = concept.args_type.join(', ');
      }

      let item = `${input}<span class="keep"><label>
${concept.description} <span style="color: #808080;">[${args_info}]</span>
</label></span>`
      radios += item;
    }

    let cand_list = `<div class="keep">${radios}</div>`;
    let submit_button = '<p><input type="submit" value="Confirm"></p>'
    let form_elements = hidden + cand_list + submit_button

    let form = `<form id="form-${mi_id}" method="POST">${form_elements}</form>`;

    // show the box
    let anno_box_content = `${title}
<div class="sidebar-box-body">
<p>Please select the most suitable one:<br/>${form}</p>
</div>`

    // for debug
    //console.log(anno_box_content);

    // write the content
    $('#anno-box').html(anno_box_content);

    // buttons by jquery-ui
    $('.sidebar-box input[type=submit]').button();
    $('.sidebar-box input[type=submit]').click(function() {
      localStorage['scroll_top'] = $(window).scrollTop();
      $('#form-' + mi_id.escape_selector()).attr('action', '/_concept');
      $('#form-' + mi_id.escape_selector()).submit();
    });

    // give colors at the same time
    $('mi').each(function() {
      give_color($(this));
    })
  }

  function show_anno_box(elem) {
    // highlight the selected element
    elem.attr('style', 'border: dotted 2px #000000; padding: 10px;');

    // prepare idf and get candidate concepts
    let idf = get_idf(elem);
    let concept_cand = get_concept_cand(idf);

    // draw the annotation box
    if(concept_cand != undefined)
      draw_anno_box(elem.attr('id'), idf, concept_cand);
  }

  $('mi').click(function() {
    // if already selected, remove it
    let old_mi_id = sessionStorage.getItem('mi_id');
    if(old_mi_id != undefined) {
      $('#' + old_mi_id.escape_selector()).removeAttr('style');
    }

    // store id of the currently selected mi
    sessionStorage['mi_id'] = $(this).attr('id');

    // show the annotation box
    show_anno_box($(this));
  })

  // keep position and sidebar content after submiting the form
  $(window).scrollTop(localStorage['scroll_top']);
  let mi_id = sessionStorage['mi_id'];
  if(mi_id != undefined) {
    show_anno_box($('#' + mi_id.escape_selector()));
  }
})

// --------------------------
// SoG Registration
// --------------------------

$(function() {
  let page_x;
  let page_y;

  function get_selected() {
    let t = '';
    if(window.getSelection) {
      t = window.getSelection();
    } else if(document.getSelection) {
      t = document.getSelection();
    } else if(document.selection) {
      t = document.selection.createRange().text;
    }
    return t;
  }

  $(document).bind('mouseup', function() {
    let selected_text = get_selected();

    if(selected_text != '') {
      $('.select-menu').css({
        'left': page_x + 5,
        'top' : page_y - 55
      }).fadeIn(200).css('display', 'flex');

      // use jquery-ui
      $('.select-menu input[type=submit]').button();

      // the add function
      $('.select-menu .sog-add').off('click');
      $('.select-menu .sog-add').on('click',
      function() {
        localStorage['scroll_top'] = $(window).scrollTop();
        let start_node = selected_text.anchorNode.parentElement;
        let stop_node = selected_text.focusNode.parentElement;
        let start_id, stop_id

        if(start_node.className == 'gd_word') {
          start_id= start_node.id;
        } else if(start_node.nextSibling.className == 'gd_word') {
          start_id = start_node.nextSibling.id;
        } else {
          alert('Invalid span for a source of grounding');
        }

        if(stop_node.className == 'gd_word') {
          stop_id = stop_node.id;
        } else if(stop_node.previousSibling.className == 'gd_word') {
          stop_id = stop_node.previousSibling.id;
        } else {
          alert('Invalid span for a source of grounding');
        }

        // post the data
        let post_data = {
          'mi_id': sessionStorage['mi_id'],
          'start_id': start_id,
          'stop_id': stop_id
        };

        $.when($.post('/_add_sog', post_data))
        .done(function() {
          // remove selection and the button
          selected_text.empty();
          $('.select-menu').fadeOut(200);

          // reload the page
          location.reload(true);
        })
        .fail(function() {
          console.log('POST sog::add failed!');
        })
      });

      // the delete function
      let e = selected_text.anchorNode.parentElement

      // show it only if SoG is selected
      if(e.getAttribute('data-sog-mi') != undefined) {
        $('.select-menu .sog-del').css('display', 'inherit');
      } else {
        $('.select-menu .sog-del').css('display', 'none');
      }

      $('.select-menu .sog-del').off('click');
      $('.select-menu .sog-del').on('click',
      function() {
        // post the data
        let post_data = {
          'mi_id': e.getAttribute('data-sog-mi'),
          'start_id': e.getAttribute('data-sog-start'),
          'stop_id': e.getAttribute('data-sog-stop'),
        };

        $.when($.post('/_delete_sog', post_data))
        .done(function() {
          // remove selection and the button
          selected_text.empty();
          $('.select-menu').fadeOut(200);

          // reload the page
          location.reload(true);
        })
        .fail(function() {
          console.log('POST sog::delete failed!');
        })
      });
    } else {
      $('.select-menu').fadeOut(200);
    }
  });
  $(document).on("mousedown", function(e){
    page_x = e.pageX;
    page_y = e.pageY;
  });
})

// --------------------------
// background color
// --------------------------

// for the identifiers that have not been annotated
function show_border(target) {
  let idf = get_idf(target);
  let concept_cand = get_concept_cand(idf);
  if(target.data('math-concept') == undefined && concept_cand != undefined)
    target.attr('mathbackground', '#D3D3D3');
}

$(function() {
  $('mi').each(function() {
    show_border($(this));
  })
});
