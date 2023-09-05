// the MioGatto client
'use strict';

// Avoid declaring global variable.
export {};

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
// Prepare the mcdict table
// --------------------------

// load from the external json file
let mcdict_edit_id: number = 0;
let mcdict = {} as {[key: string]: {[key: string]: Concept[]}};
$.ajax({
  url: '/mcdict.json',
  dataType: 'json',
  async: false,
  success: function(data) {
    // Data is extended to include mcdict version.
    mcdict_edit_id = data[0];
    mcdict = data[1];
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

// --------------------------
// Functions
// --------------------------

function edit_concept(idf: Identifier, concept_id: number) {
  let concept_dialog = $('#concept-dialog-template').clone();
  concept_dialog.removeAttr('id');
  let form = concept_dialog.find('#concept-form');
  form.attr('action', '/_update_concept_for_edit_mcdict');

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
        form.append(`<input type="hidden" name="mcdict_edit_id" value="${mcdict_edit_id}" />`)
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

// --------------------------
// Edit mcdict
// --------------------------

// convert hex string to UTF-8 string
function hex_decode(str: string) {
  let bytes: number[] = Array();

  // Convert hex to int.
  for (let i = 0; i < str.length ; i += 2) {
    bytes.push(parseInt(str.slice(i, i + 2), 16));
  }

  //console.log(new Uint8Array(bytes));

  let decoded: string = (new TextDecoder()).decode(new Uint8Array(bytes));
  return decoded;
}

// Show identifiers in edit-mcdict-box.
$(function () {

  let all_idf_content = '';
  //let table_header = '<tr><th>Identifier</th><th>Description</th><th>Affix</th><th>Arity</th><th>#Occurence</th><th>#Sog</th><th>Edit</th></tr>';
  let table_header = '<tr><th>Identifier</th><th>Description</th><th>Affix</th><th>Arity</th><th>Edit</th></tr>';
  let table_content = '';

  for (let idf_hex in mcdict) {
    for (let idf_var in mcdict[idf_hex]) {

      // Retrive identifier.
      let idf_str = hex_decode(idf_hex);
      let idf_elem = '';

      if (idf_var != 'default') {
        idf_elem = `<math><mi mathvariant=${idf_var}>${idf_str}</mi></math>`;
      } else {
        // Do not set mathvariant.
        idf_elem = `<math><mi>${idf_str}</mi></math>`;
      }

      // Retrive concepts.

      let candidate_rows = ``;

      if (mcdict[idf_hex][idf_var].length == 0) {
        // If there is no candidate concepts.
        candidate_rows = `<tr><td align="center">${idf_elem}</td><td colspan="4">No candidate concepts</td></tr>`;

      } else {
        let cand_i = 0;

        for (let concept_id in mcdict[idf_hex][idf_var]) {
          let concept: Concept = mcdict[idf_hex][idf_var][concept_id];

          if (concept.description != undefined) {

            let args_info = 'NONE';
            if(concept.affixes.length > 0) {
              args_info = concept.affixes.join(', ');
            }

            let idf_column = '';
            if (cand_i == 0){
              idf_column = `<td  align="center" rowspan="${mcdict[idf_hex][idf_var].length}">${idf_elem}</td>`;
            }

            let concept_row = `<tr>${idf_column}<td>${concept.description}</td><td><span style="color: #808080;">[${args_info}]</span></td><td><span style="color: #808080;">${concept.arity}</span></td><td><a class="edit-concept-mcdict" data-idf-hex="${idf_hex}" data-idf-var="${idf_var}" data-concept="${concept_id}" href="javascript:void(0);">edit</a></td></tr>`;

//            let item = `<span class="keep"><label for="c${concept_id}">
//${concept.description} <span style="color: #808080;">[${args_info}] (arity: ${concept.arity})</span>
//(<a class="edit-concept-mcdict" data-idf-hex="${idf_hex}" data-idf-var="${idf_var}" data-concept="${concept_id}" href="javascript:void(0);">edit</a>)
//</label></span>`;

            candidate_rows += concept_row;

            cand_i += 1;

          }
        }
      }

      table_content += candidate_rows

    }
  }

  let content = `<table border="1">${table_header}${table_content}</table>`;

  let mcdict_edit_box = $('#edit-mcdict-box');
  mcdict_edit_box.html(content)


  // enable concept dialogs
  $('a.edit-concept-mcdict').on('click', function() {
    let idf_hex = $(this).attr('data-idf-hex');
    let idf_var = $(this).attr('data-idf-var');
    let concept_id = $(this).attr('data-concept');

    let idf = {'hex': idf_hex, 'var': idf_var, 'concept': concept_id} as Identifier;

    edit_concept(idf, Number(concept_id));
  });

});
