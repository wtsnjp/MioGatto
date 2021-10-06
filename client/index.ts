// the MioGatto client
'use strict';

// --------------------------
// Type declaration
// --------------------------

interface Identifier {
  hex: string;
  var: string;
  concept?: number;
}

interface Concept {
  args_type: string[];
  arity: number;
  description: string;
  color?: string;
}

interface Source {
  mi_id: string;
  start_id: string;
  stop_id: string;
}

// --------------------------
// utility
// --------------------------

// escape for jQuery selector
function escape_selector(raw: string) {
  return raw.replace(/[ !"#$%&'()*+,.\/:;<=>?@\[\\\]^`{|}~]/g, "\\$&");
}

// convert UTF-8 string to hex string
function hex_encode(str: string) {
  let arr = Array.from((new TextEncoder()).encode(str)).map(
    v => v.toString(16));
  return arr.join('');
}

// construct the idf dict from a mi element
function get_idf(elem: JQuery<any>) {
  let idf = {} as Identifier;
  idf.hex = hex_encode(elem.text());
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
  if(concept_cand != undefined)
    idf.concept = Number(concept_cand);

  return idf;
}

// convert color code from hex to rgb
function hex2rgb(hex: string) {
  if(hex.slice(0, 1) == "#") {
    hex = hex.slice(1);
  }
  if(hex.length == 3) {
    hex = hex.slice(0, 1) + hex.slice(0, 1) + hex.slice(1, 2) + hex.slice(1, 2) + hex.slice(2, 3) + hex.slice(2, 3);
  }

  return [hex.slice(0, 2), hex.slice(2, 4), hex.slice(4, 6)].map(function(str) {
    return parseInt(str, 16);
  });
}

// --------------------------
// Sidebar
// --------------------------

$(function() {
  $('.sidebar-tab input.tab-title').each(function() {
    let tab_name = this.id;
    if(localStorage[tab_name] == 'true') {
      $(`#${tab_name}`).prop('checked', true);
    }

    $(`#${tab_name}`).on('change', function() {
      if($(this).prop('checked')) {
        console.log(`${tab_name}: true`);
        localStorage[tab_name] = true;
      } else {
        console.log(`${tab_name}: false`);
        localStorage[tab_name] = false;
      }
    });
  });
});

// --------------------------
// prepare the mcdict table
// --------------------------

// load from the external json file
let mcdict = {} as {[key: string]: {[key: string]: Concept[]}};
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
function get_concept(idf: Identifier) {
  if(idf.concept != undefined) {
    return mcdict[idf.hex][idf.var][idf.concept];
  } else {
    return undefined;
  }
}

function get_concept_cand(idf: Identifier) {
  if(mcdict[idf.hex] != undefined)
    return mcdict[idf.hex][idf.var]; // can be undefined
}

// --------------------------
// mathcolor
// --------------------------

function give_color(target: JQuery) {
  let idf = get_idf(target);
  let concept = get_concept(idf);
  if(concept != undefined && concept.color != undefined) {
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
let sog = {} as {sog: Source[]};
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
      sog_nodes = $('#' + escape_selector(s.start_id));
    } else {
      let start_node = $('#' + escape_selector(s.start_id));
      let stop_node = $('#' + escape_selector(s.stop_id));

      sog_nodes = start_node.nextUntil('#' + escape_selector(s.stop_id)).addBack().add(stop_node);
    }

    // get the concept for the SoG
    let idf = get_idf($('#' + escape_selector(s.mi_id)));
    let concept = get_concept(idf);

    // no hilight if no concept has been asigned
    if (concept == undefined || concept.color == undefined)
      continue;

    // highlight it!
    sog_nodes.css('background-color', `rgba(${hex2rgb(concept.color).join()},0.3)`);
    sog_nodes.attr({
      'data-sog-mi': s.mi_id,
      'data-sog-start': s.start_id,
      'data-sog-stop': s.stop_id,
    });
  }
});

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
      let concept = get_concept(idf);
      if(concept != undefined) {
        return concept.description;
      } else {
        return '(No description)';
      }
    },
    open: function(_event, _ui) {
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
  function draw_anno_box(mi_id: string, idf: Identifier, concept_cand: Concept[]) {
    // construct the form with the candidate list
    let hidden = `<input type="hidden" name="mi_id" value="${mi_id}" />`;
    let radios = '';

    for(let concept_id in concept_cand) {
      let concept = concept_cand[concept_id];

      let check = (Number(concept_id) == idf.concept) ? 'checked' : '';
      let input = `<input type="radio" name="concept" id="c${concept_id}" value="${concept_id}" ${check} />`;

      let args_info = 'NONE';
      if(concept.args_type.length > 0) {
        args_info = concept.args_type.join(', ');
      }

      let item = `${input}<span class="keep"><label for="c${concept_id}">
${concept.description} <span style="color: #808080;">[${args_info}]</span>
(<a class="edit-concept" data-mi="${mi_id}" data-concept="${concept_id}" href="javascript:void(0);">edit</a>)
</label></span>`
      radios += item;
    }

    let cand_list = `<div class="keep">${radios}</div>`;
    let buttons = '<p><button id="choose-concept">Choose</button> <button id="new-concept" type="button">New</button></p>'
    let form_elements = hidden + cand_list + buttons

    let form = `<form id="form-${mi_id}" action="/_concept" method="POST">${form_elements}</form>`;

    // show the box
    let id_span = `ID: <span style="font-family: monospace;">${mi_id}</span>`
    let anno_box_content = `<p>${id_span}<hr color="#FFF">${form}</p>`

    // for debug
    //console.log(anno_box_content);

    // write the content
    $('#anno-box').html(anno_box_content);

    // send chosen concept
    $('button#choose-concept').button();
    $('button#choose-concept').on('click', function() {
      if($(`#form-${escape_selector(mi_id)} input:checked`).length > 0) {
        localStorage['scroll_top'] = $(window).scrollTop();
      } else {
        alert('Please select a concept.');
        return false;
      }
    });

    // enable concept dialogs
    new_concept_button(idf);
    $('a.edit-concept').on('click', function() {
      let mi_id = $(this).attr('data-mi');
      let concept_id = $(this).attr('data-concept');

      if(mi_id != undefined && concept_id != undefined) {
        let idf = get_idf($('#' + escape_selector(mi_id)));
        edit_concept(idf, Number(concept_id));
      }
    });

    // give colors at the same time
    $('mi').each(function() {
      give_color($(this));
    })
  }

  function show_anno_box(mi: JQuery) {
    // highlight the selected element
    mi.attr('style', 'border: dotted 2px #000000; padding: 10px;');

    // prepare idf and get candidate concepts
    let idf = get_idf(mi);
    let concept_cand = get_concept_cand(idf);

    // draw the annotation box
    let mi_id = mi.attr('id');
    if(concept_cand != undefined && mi_id != undefined) {
      if(concept_cand.length > 0) {
        draw_anno_box(mi_id, idf, concept_cand);
      } else {
        let id_span = `ID: <span style="font-family: monospace;">${mi_id}</span>`
        let no_concept = '<p>No concept is available.</p>'
        let button = '<p><button id="new-concept" type="button">New</button></p>'
        let msg = `<p>${id_span}<hr color="#FFF">${no_concept}${button}</p>`
        $('#anno-box').html(msg);

        // enable the button
        new_concept_button(idf);
      }
    }
  }

  function new_concept_button(idf: Identifier) {
    $('button#new-concept').button();
    $('button#new-concept').on('click', function() {
      let concept_dialog = $('.concept-dialog').clone();
      concept_dialog.removeClass('concept-dialog');
      let form = concept_dialog.find('#concept-form');
      form.attr('action', '/_new_concept');

      concept_dialog.dialog({
        modal: true,
        title: 'New Concept',
        width: 500,
        buttons: {
          'OK': function() {
            localStorage['scroll_top'] = $(window).scrollTop();
            form.append(`<input type="hidden" name="idf_hex" value="${idf.hex}" />`);
            form.append(`<input type="hidden" name="idf_var" value="${idf.var}" />`);
            form.trigger("submit");
          },
          'Cancel': function() {
            $(this).dialog('close');
          }
        }
      });
    });
  }

  function edit_concept(idf: Identifier, concept_id: number) {
    let concept_dialog = $('#concept-dialog-template').clone();
    concept_dialog.removeAttr('id');
    let form = concept_dialog.find('#concept-form');
    form.attr('action', '/_update_concept');

    // put the current values
    let concept = mcdict[idf.hex][idf.var][concept_id];
    form.find('textarea').text(concept.description);
    form.find('input[name="arity"]').attr('value', concept.arity);
    concept.args_type.forEach(function(value, idx) {
      form.find(`select[name="args_type${idx}"]`).find(
        `option[value="${value}"]`).prop('selected', true);
    })

    concept_dialog.dialog({
      modal: true,
      title: 'Edit Concept',
      width: 500,
      buttons: {
        'OK': function() {
          localStorage['scroll_top'] = $(window).scrollTop();
          form.append(`<input type="hidden" name="idf_hex" value="${idf.hex}" />`)
          form.append(`<input type="hidden" name="idf_var" value="${idf.var}" />`)
          form.append(`<input type="hidden" name="concept_id" value="${concept_id}" />`)
          form.trigger("submit");
        },
        'Cancel': function() {
          $(this).dialog('close');
        }
      }
    });
  }

  $('mi').on('click', function() {
    // if already selected, remove it
    let old_mi_id = sessionStorage.getItem('mi_id');
    if(old_mi_id != undefined) {
      $('#' + escape_selector(old_mi_id)).removeAttr('style');
    }

    // store id of the currently selected mi
    sessionStorage['mi_id'] = $(this).attr('id');

    // show the annotation box
    show_anno_box($(this));
  });

  // keep position and sidebar content after submiting the form
  $(window).scrollTop(localStorage['scroll_top']);
  let mi_id = sessionStorage['mi_id'];
  if(mi_id != undefined) {
    show_anno_box($('#' + escape_selector(mi_id)));
  }
});

// --------------------------
// SoG Registration
// --------------------------

function get_selection(): [
    string | undefined, string | undefined, HTMLElement | undefined] {
  // get selection
  let selected_text;
  if(window.getSelection) {
    selected_text = window.getSelection();
  } else if(document.getSelection) {
    selected_text = document.getSelection();
  }

  // return undefineds for unproper cases
  if(selected_text == undefined || selected_text.type != 'Range')
    return [undefined, undefined, undefined];

  let anchor_node = selected_text?.anchorNode?.parentElement;
  let focus_node = selected_text?.focusNode?.parentElement;
  if(anchor_node == undefined || focus_node == undefined)
    return [undefined, undefined, undefined];

  if($(anchor_node).parents('.main').length == 0 || $(focus_node).parents('.main').length == 0)
    return [undefined, undefined, undefined];

  // determine which (start|stop)_node
  let anchor_rect = anchor_node.getBoundingClientRect();
  let focus_rect = focus_node.getBoundingClientRect();

  let start_node, stop_node;
  if(anchor_rect.top < focus_rect.top) {
    [start_node, stop_node] = [anchor_node, focus_node];
  } else if(anchor_rect.top == focus_rect.top && anchor_rect.left <= focus_rect.left) {
    [start_node, stop_node] = [anchor_node, focus_node];
  } else {
    [start_node, stop_node] = [focus_node, anchor_node];
  }

  // get start_id and stop_id
  let start_id, stop_id;

  if(start_node.className == 'gd_word') {
    start_id= start_node.id;
  } else if(start_node.nextElementSibling?.className == 'gd_word') {
    start_id = start_node.nextElementSibling.id;
  } else {
    console.warn('Invalid span for a source of grounding');
  }

  if(stop_node.className == 'gd_word') {
    stop_id = stop_node.id;
  } else if(stop_node.previousElementSibling?.className == 'gd_word') {
    stop_id = stop_node.previousElementSibling.id;
  } else {
    console.warn('Invalid span for a source of grounding');
  }

  return [start_id, stop_id, start_node];
}

$(function() {
  let page_x: number;
  let page_y: number;

  $(document).on('mouseup', function() {
    $('.select-menu').css('display', 'none');
    let [start_id, stop_id, parent] = get_selection();

    if(parent == undefined)
      return;

    // ----- Action SoG add -----
    let mi_id = sessionStorage['mi_id'];

    // show it only if an mi with concept annotation selected
    if(mi_id != undefined) {
      let idf = get_idf($('#' + escape_selector(mi_id)));
      let concept = get_concept(idf);
      if(concept != undefined) {
        $('.select-menu').css({
          'left': page_x + 5,
          'top' : page_y - 55
        }).fadeIn(200).css('display', 'flex');
      }
    }

    // use jquery-ui
    $('.select-menu input[type=submit]').button();

    // the add function
    $('.select-menu .sog-add').off('click');
    $('.select-menu .sog-add').on('click',
    function() {
      $('.select-menu').css('display', 'none');

      // post the data
      let post_data = {
        'mi_id': mi_id,
        'start_id': start_id,
        'stop_id': stop_id
      };

      localStorage['scroll_top'] = $(window).scrollTop();

      $.when($.post('/_add_sog', post_data))
      .done(function() {
        location.reload();
      })
      .fail(function() {
        console.error('Failed to POST _add_sog!');
      });
    });

    // ----- Action SoG delete -----
    // show it only if SoG is selected
    if(parent?.getAttribute('data-sog-mi') != undefined) {
      $('.select-menu .sog-del').css('display', 'inherit');
    } else {
      $('.select-menu .sog-del').css('display', 'none');
    }

    $('.select-menu .sog-del').off('click');
    $('.select-menu .sog-del').on('click',
    function() {
      $('.select-menu').css('display', 'none');

      // make sure parent exists
      // Note: the button is shown only if it exists
      if(parent == undefined)
        return;

      // post the data
      let post_data = {
        'mi_id': parent.getAttribute('data-sog-mi'),
        'start_id': parent.getAttribute('data-sog-start'),
        'stop_id': parent.getAttribute('data-sog-stop'),
      };

      localStorage['scroll_top'] = $(window).scrollTop();

      $.when($.post('/_delete_sog', post_data))
      .done(function() {
        location.reload();
      })
      .fail(function() {
        console.error('Failed to POST _delete_sog!');
      })
    });
  });

  $(document).on("mousedown", function(e) {
    page_x = e.pageX;
    page_y = e.pageY;
  });
});

// --------------------------
// background color
// --------------------------

// for the identifiers that have not been annotated
function show_border(target: JQuery) {
  let idf = get_idf(target);
  let concept_cand = get_concept_cand(idf);
  if(target.data('math-concept') == undefined && concept_cand != undefined)
    target.attr('mathbackground', '#D3D3D3');
}

$(function() {
  $('mi').each(function() {
    show_border($(this));
  });
});
