// the MioGatto client
'use strict';

import {Identifier, Concept, dfs_mis, get_idf, mcdict, mcdict_edit_id, sog, escape_selector} from "./common";

// --------------------------
// Edit mcdict
// --------------------------

let mi_list: Identifier[] = [];

// Update mi_list after loading html.
$(function() {

  // Load mi_list.
  for (let mi_jquery of dfs_mis($(":root"))) {

    mi_list.push(get_idf(mi_jquery));
  }

});

// Sending a form specific to edit_mcdict
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

// Count the annotated idfs.
function count_idf_progress(idf_hex: string, idf_var: string): [number, number] {
  let idf_annotated = 0;
  let idf_occur = 0;

  for (let mi of mi_list) {

    if ((mi.hex == idf_hex) && (mi.var == idf_var)) {
      idf_occur += 1;

      // Check if annotated.
      if (mi.concept != undefined) {
        idf_annotated += 1;
      }

    }
  }

  return [idf_annotated, idf_occur];
}

// Count the number of occurences.
function count_occur(idf_hex: string, idf_var: string, concept_id: number): number {
  let count = 0;

  for (let mi of mi_list) {

    if ((mi.hex == idf_hex) && (mi.var == idf_var) && (mi.concept != undefined) && (mi.concept == concept_id)) {
      count += 1;
    }
  }

  return count;
}

// Count the number of sogs.
function count_sog(idf_hex: string, idf_var: string, concept_id: number): number {
  let count = 0;

  for (let s of sog.sog) {
    let sog_idf = get_idf($('#' + escape_selector(s.mi_id)));

    if ((sog_idf.hex == idf_hex) && (sog_idf.var == idf_var) && (sog_idf.concept != undefined) && (sog_idf.concept == concept_id)) {
      count += 1;
    }
  }

  return count;
}

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

  let table_header = '<tr><th>Identifier</th><th>Progress</th><th>Description</th><th>Affix</th><th>Arity</th><th>#Occur</th><th>#Sog</th><th>Edit</th></tr>';

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
        // Calculate the progress for each identifier.
        let idf_progress: [number, number] = count_idf_progress(idf_hex, idf_var);

        let idf_annotated = idf_progress[0];
        let idf_occur = idf_progress[1];

        candidate_rows = `<tr><td align="center">${idf_elem}</td><td>${idf_annotated}/${idf_occur}</td><td colspan="6">No candidate concepts</td></tr>`;

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

              // Calculate the progress for each identifier.
              let idf_progress: [number, number] = count_idf_progress(idf_hex, idf_var);

              let idf_annotated = idf_progress[0];
              let idf_occur = idf_progress[1];

              idf_column = `<td  align="center" rowspan="${mcdict[idf_hex][idf_var].length}">${idf_elem}</td><td  align="center" rowspan="${mcdict[idf_hex][idf_var].length}">${idf_annotated}/${idf_occur}</td>`;
            }

            // Calculate the number of occurences and sogs.

            let num_occur = count_occur(idf_hex, idf_var, Number(concept_id));

            let num_sogs = count_sog(idf_hex, idf_var, Number(concept_id));

            let concept_row = `<tr>${idf_column}<td>${concept.description}</td><td>${args_info}</td><td align="right">${concept.arity}</td><td align="right">${num_occur}</td><td align="right">${num_sogs}</td><td><a class="edit-concept-mcdict" data-idf-hex="${idf_hex}" data-idf-var="${idf_var}" data-concept="${concept_id}" href="javascript:void(0);">edit</a></td></tr>`;

            candidate_rows += concept_row;

            cand_i += 1;

          }
        }
      }

      table_content += candidate_rows

    }
  }

  let content = `<table border="1" cellpadding="5">${table_header}${table_content}</table>`;

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
