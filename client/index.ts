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
  affixes: string[];
  arity: number;
  description: string;
  color?: string;
}

interface Source {
  mi_id: string;
  start_id: string;
  stop_id: string;
  type: number;  // 0: declaration, 1: definition, 2: others
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
// Options
// --------------------------

let miogatto_options: { [name: string]: boolean } = {
  limited_highlight: false,
  show_definition: false,
}

$(function() {
  let input_opt_hl = $('#option-limited-highlight');
  let input_opt_def = $('#option-show-definition');

  // first time check
  if(localStorage['option-limited-highlight'] == 'true') {
    input_opt_hl.prop('checked', true);
    miogatto_options.limited_highlight = true
  } else {
    miogatto_options.limited_highlight = false
  }

  if(localStorage['option-show-definition'] == 'true') {
    input_opt_def.prop('checked', true);
    miogatto_options.show_definition = true
  } else {
    miogatto_options.show_definition = false
  }

  give_sog_highlight();

  // toggle
  input_opt_hl.on('click', function() {
    if($(this).prop('checked')) {
      localStorage['option-limited-highlight'] = 'true';
      miogatto_options.limited_highlight = true
    } else {
      localStorage['option-limited-highlight'] = 'false';
      miogatto_options.limited_highlight = false
    }
    give_sog_highlight();
  });

  input_opt_def.on('click', function() {
    if($(this).prop('checked')) {
      localStorage['option-show-definition'] = 'true';
      miogatto_options.show_definition = true
    } else {
      localStorage['option-show-definition'] = 'false';
      miogatto_options.show_definition = false
    }
    give_sog_highlight();
  });
});

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
        localStorage[tab_name] = true;
      } else {
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

function apply_highlight(sog_nodes: JQuery, idf: Identifier, sog: Source) {
  remove_highlight(sog_nodes);

  let concept = get_concept(idf);
  if (concept == undefined || concept.color == undefined) {
    // red underline if concept is unassigned
    sog_nodes.css('border-bottom', 'solid 2px #FF0000');
  } else {
    // highlight it!
    sog_nodes.css('background-color', `rgba(${hex2rgb(concept.color).join()},0.3)`);
    if(miogatto_options.show_definition && sog.type == 1) {
      sog_nodes.css('border-bottom', 'solid 3px');
    }
  }

  // embed SoG information for removing
  sog_nodes.attr({
    'data-sog-mi': sog.mi_id,
    'data-sog-type': sog.type,
    'data-sog-start': sog.start_id,
    'data-sog-stop': sog.stop_id,
  });
}

function remove_highlight(sog_nodes: JQuery) {
  sog_nodes.css('border-bottom', '');
  sog_nodes.css('background-color', '');
}

function give_sog_highlight() {
  // remove highlight
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

    let sog_idf = get_idf($('#' + escape_selector(s.mi_id)));

    if(miogatto_options.limited_highlight && sessionStorage['mi_id'] != undefined) {
      let cur_mi = $('#' + escape_selector(sessionStorage['mi_id']));
      let cur_idf = get_idf(cur_mi);
      if(!(cur_idf.hex == sog_idf.hex && cur_idf.var == sog_idf.var)) {
        remove_highlight(sog_nodes);
      }
    }
  }
  // apply highlight
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

    let sog_idf = get_idf($('#' + escape_selector(s.mi_id)));

    if(miogatto_options.limited_highlight && sessionStorage['mi_id'] != undefined) {
      let cur_mi = $('#' + escape_selector(sessionStorage['mi_id']));
      let cur_idf = get_idf(cur_mi);
      if(cur_idf.hex == sog_idf.hex && cur_idf.var == sog_idf.var) {
        apply_highlight(sog_nodes, sog_idf, s);
      } 
    } else {
      // always apply
      apply_highlight(sog_nodes, sog_idf, s);
    }
  }
}

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
        let args_info = 'NONE';
        if(concept.affixes.length > 0) {
          args_info = concept.affixes.join(', ');
        }
        return `${concept.description} <span style="color: #808080;">[${args_info}] (arity: ${concept.arity})</span>`;
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
      if(concept.affixes.length > 0) {
        args_info = concept.affixes.join(', ');
      }

      let item = `${input}<span class="keep"><label for="c${concept_id}">
${concept.description} <span style="color: #808080;">[${args_info}] (arity: ${concept.arity})</span>
(<a class="edit-concept" data-mi="${mi_id}" data-concept="${concept_id}" href="javascript:void(0);">edit</a>)
</label></span>`
      radios += item;
    }

    let cand_list = `<div class="keep">${radios}</div>`;
    let buttons = '<p><button id="assign-concept">Assign</button> <button id="remove-concept" type="button">Remove</button> <button id="new-concept" type="button">New</button></p>'
    let form_elements = hidden + cand_list + buttons

    let form_str = `<form id="form-${mi_id}" method="POST">${form_elements}</form>`;

    // show the box
    let id_span = `ID: <span style="font-family: monospace;">${mi_id}</span>`
    let anno_box_content = `<p>${id_span}<hr color="#FFF">${form_str}</p>`

    //console.debug(anno_box_content);

    // write the content
    let anno_box = $('#anno-box')
    anno_box.html(anno_box_content);

    // assign chosen concept
    $('button#assign-concept').button();
    $('button#assign-concept').on('click', function() {
      let form = anno_box.find(`#form-${escape_selector(mi_id)}`);
      if($(`#form-${escape_selector(mi_id)} input:checked`).length > 0) {
        localStorage['scroll_top'] = $(window).scrollTop();
        form.attr('action', '/_concept');
        form.trigger("submit");
      } else {
        alert('Please select a concept.');
        return false;
      }
    });

    // remove assignment
    $('button#remove-concept').button();
    $('button#remove-concept').on('click', function() {
      let form = anno_box.find(`#form-${escape_selector(mi_id)}`);
      form.attr('action', '/_remove_concept');
      form.trigger("submit");
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
      let concept_dialog = $('#concept-dialog-template').clone();
      concept_dialog.attr('id', 'concept-dialog');
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
        },
        close: function() {
          $(this).remove();
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
    concept.affixes.forEach(function(value, idx) {
      form.find(`select[name="affixes${idx}"]`).find(
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

    // also update SoG highlight
    if(localStorage['option-limited-highlight'] == 'true') {
      miogatto_options.limited_highlight = true;
    }
    give_sog_highlight();
  });

  // keep position and sidebar content after submiting the form
  // This '$(window).scrollTop' seems redundant but somehow fixes the page position problems...
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

  $(document).on('mouseup', function(e) {
    page_x = e.pageX;
    page_y = e.pageY;
  
    $('.sog-menu').css('display', 'none');
    let [start_id, stop_id, parent] = get_selection();

    if(parent == undefined)
      return;

    // use jquery-ui
    $('.sog-menu input[type=submit]').button();

    // ----- Action SoG add -----
    let mi_id = sessionStorage['mi_id'];

    // show it only if an mi with concept annotation selected
    if(mi_id != undefined) {
      let idf = get_idf($('#' + escape_selector(mi_id)));
      let concept = get_concept(idf);
      if(concept != undefined) {
        $('.sog-menu').css({
          'left': page_x,
          'top' : page_y - 20
        }).fadeIn(200).css('display', 'flex');
      }
    }

    // show the current target
    let id_span = `<span style="font-family: monospace;">${mi_id}</span>`;
    let add_menu_info = `<p>Selected mi: ${id_span}</p>`;
    $('.sog-add-menu-info').html(add_menu_info);

    // the add function
    $('.sog-menu .sog-add').off('click');
    $('.sog-menu .sog-add').on('click',
    function() {
      $('.sog-menu').css('display', 'none');

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

    // ----- SoG menu -----
    // show it only if SoG is selected
    if(parent?.getAttribute('data-sog-mi') != undefined) {
      $('.sog-mod-menu').css('display', 'inherit');
    } else {
      $('.sog-mod-menu').css('display', 'none');
    }

    let sog_mi_id = parent.getAttribute('data-sog-mi');
    let sog_type_int = Number(parent.getAttribute('data-sog-type'));
    let sog_start_id = parent.getAttribute('data-sog-start');
    let sog_stop_id = parent.getAttribute('data-sog-stop');

    let sog_type = 'unknown';
    if(sog_type_int == 0) {
      sog_type = 'declaration';
    } else if(sog_type_int == 1) {
      sog_type = 'definition';
    } else if(sog_type_int == 2) {
      sog_type = 'others';
    }
    let id_span_for_sog = `<span style="font-family: monospace;">${sog_mi_id}</span>`;
    let mod_menu_info = `<p>SoG for ${id_span_for_sog}<br/>Type: ${sog_type}</p>`;
    $('.sog-mod-menu-info').html(mod_menu_info);

    // ----- Action SoG change type -----
    $('.sog-menu .sog-type').off('click');
    $('.sog-menu .sog-type').on('click',
    function() {
      $('.sog-menu').css('display', 'none');

      // make sure parent exists
      // Note: the button is shown only if it exists
      if(parent == undefined)
        return;

      let sog_type_dialog = $('#sog-type-dialog-template').clone();
      sog_type_dialog.attr('id', 'sog-type-dialog');
      sog_type_dialog.removeClass('sog-type-dialog');

      let form = sog_type_dialog.find('#sog-type-form');
      form.attr('action', '/_change_sog_type');

      sog_type_dialog.find(`input[value="${sog_type_int}"]`).prop('checked', true);

      sog_type_dialog.dialog({
        modal: true,
        title: 'Change SoG Type',
        width: 200,
        buttons: {
          'OK': function() {
            localStorage['scroll_top'] = $(window).scrollTop();
            form.append(`<input type="hidden" name="mi_id" value="${sog_mi_id}" />`);
            form.append(`<input type="hidden" name="start_id" value="${sog_start_id}" />`);
            form.append(`<input type="hidden" name="stop_id" value="${sog_stop_id}" />`);
            form.trigger("submit");
          },
          'Cancel': function() {
            $(this).dialog('close');
          }
        },
        close: function() {
          $(this).remove();
        }
      });
    });

    // ----- Action SoG delete -----
    $('.sog-menu .sog-del').off('click');
    $('.sog-menu .sog-del').on('click',
    function() {
      $('.sog-menu').css('display', 'none');

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

// --------------------------
// Keybord shortcuts
// --------------------------

function select_concept(num: number) {
  let elem = $(`#c${num - 1}`);
  if(elem[0]) {
    $('input[name="concept"]').prop('checked', false);
    $(`#c${num - 1}`).prop('checked', true);
  }
}

for (let i=1; i<10; i++) {
  $(document).on('keydown', function(event) {
    if(!$('#concept-dialog')[0]) {
      if(event.key == i.toString(10)) {
        select_concept(i);
      }
    }
  });
}

$(document).on('keydown', function(event) {
  if(event.key == 'Enter') {
    if(!$('#concept-dialog')[0]) {
      $('#assign-concept').trigger('click');
    }
  }
});

$(document).on('keydown', function(event) {
  if(event.key == 'j') {
    $('button#jump-to-next-unannotated-mi').trigger('click');
  } else if (event.key == 'k') {
    $('button#jump-to-prev-unannotated-mi').trigger('click');
  }
});

// --------------------------
// Error from the server
// --------------------------

$(function() {
  if($('#error-message').text().length != 0) {
    $('#error-dialog').dialog({
      dialogClass: 'error-dialog',
      modal: true,
      title: 'Error',
      buttons: {
        "OK": function() {
          $(this).dialog('close');
        }
      }
    });
  }
});

// --------------------------
// Utilities 
// --------------------------


function dfs_mis(cur_node: JQuery<any>): JQuery<any>[] {

  let obtained_mis: JQuery<any>[] = [];

  // Add current node if its mi.
  // Only consider the mis in mcdict.
  if((cur_node.is('mi')) && (get_concept_cand(get_idf(cur_node)) != undefined)){
    obtained_mis =  [cur_node];
  }

  // DFS search the children.
  for (let i = 0; i < cur_node.children().length; i++){
    let child = cur_node.children().eq(i);
    obtained_mis = obtained_mis.concat(dfs_mis(child));
  }

  return obtained_mis;
}

let mi_list: JQuery[] = [];
let mi_id2index: {[mi_id: string]: number} = {};

// Update mi_list after loading html.
$(function() {
  // Load mi_list.
  mi_list = dfs_mis($(":root"));

  //console.log(mi_list);

  for (let i = 0; i < mi_list.length; i++) {
    let mi_id = mi_list[i].attr('id');

    if (mi_id != undefined) {
      mi_id2index[mi_id] = i;
    } else {
      console.error('mi_id undefiend!');
      console.error(i);
      console.error(mi_list[i]);
    }
  }
});

// Search the next unannotated mi starting from start_index.
function get_next_unannotated_mi_index(start_index: number): number | undefined {
  // Loop over mi_list at most once.
  for (let count = 0; count < mi_list.length; count++) {
    let index: number = (start_index + count) % mi_list.length;

    let mi: JQuery<any> = mi_list[index];

    // Check if the mi is unannotated.
    if(get_concept(get_idf(mi)) == undefined){
      return index;
    }
  }
  // Return undefined if there is no unannotated mi.
  return undefined;
}

// Search the next unannotated mi starting from start_index.
function get_prev_unannotated_mi_index(start_index: number): number | undefined {
  // Loop over mi_list at most once.
  for (let count = mi_list.length; count > 0; count--) {
    let index: number = (start_index + count) % mi_list.length;

    let mi: JQuery<any> = mi_list[index];

    // Check if the mi is unannotated.
    if(get_concept(get_idf(mi)) == undefined){
      return index;
    }
  }
  // Return undefined if there is no unannotated mi.
  return undefined;
}

$(function() {
  $('button#jump-to-next-unannotated-mi').button();
  $('button#jump-to-next-unannotated-mi').on('click', function() {
    // First set this value so that the next mi is the first unannotated mi when mi_id is not stored.
    let current_index: number = mi_list.length - 1

    // Use the stored mi_id if there is.
    if ((sessionStorage['mi_id'] != undefined) && (sessionStorage['mi_id'] in mi_id2index)) {
      current_index = mi_id2index[sessionStorage['mi_id']];
    }

    // Start searching the next unannotated mi from start_index.
    let start_index: number = (current_index + 1) % mi_list.length

    let next_index: number | undefined = get_next_unannotated_mi_index(start_index);

    // Do nothing if there is no unannotated mi.
    if (next_index != undefined) {
      let next_unannotated_mi = mi_list[next_index]

      let jump_dest = next_unannotated_mi?.offset()?.top;
      let window_height = $(window).height();
      if(jump_dest != undefined && window_height != undefined){
        $(window).scrollTop(jump_dest - (window_height / 2));

        // Click the next mi.
        next_unannotated_mi.trigger('click');
      }
    }
  });

  $('button#jump-to-prev-unannotated-mi').button();
  $('button#jump-to-prev-unannotated-mi').on('click', function() {
    // First set this value so that the prev mi is the last unannotated mi when mi_id is not stored.
    let current_index: number = 0

    // Use the stored mi_id if there is.
    if ((sessionStorage['mi_id'] != undefined) && (sessionStorage['mi_id'] in mi_id2index)) {
      current_index = mi_id2index[sessionStorage['mi_id']];
    }

    // Start searching the prev unannotated mi from start_index.
    let start_index: number = (current_index + mi_list.length - 1) % mi_list.length

    let prev_index: number | undefined = get_prev_unannotated_mi_index(start_index);

    // Do nothing if there is no unannotated mi.
    if (prev_index != undefined) {
      let prev_unannotated_mi = mi_list[prev_index]

      let jump_dest = prev_unannotated_mi?.offset()?.top;
      let window_height = $(window).height();
      if(jump_dest != undefined && window_height != undefined){
        $(window).scrollTop(jump_dest - (window_height / 2));

        // Click the prev mi.
        prev_unannotated_mi.trigger('click');
      }
    }
  });

});

// Set page position at the last
$(function() {
  $(window).scrollTop(localStorage['scroll_top']);
})
