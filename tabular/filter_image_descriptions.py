#!/usr/bin/env python

import argparse
import json
from pathlib import Path

import pandas as pd

# BIDS datatypes are folder names under the subject folder, typically related to imaging modalities (anat, dwi, func, etc.)
# BIDS suffixes are the last suffix before the file extension in a filename, typically related to image contrast (T1w, etc.)
# https://bids-specification.readthedocs.io/en/stable/05-derivatives/02-common-data-types.html#preprocessed-or-cleaned-data
from tabular.filters import (
    DATATYPE_ANAT, DATATYPE_DWI, DATATYPE_FUNC, 
    SUFFIX_T1, SUFFIX_T2, SUFFIX_T2_STAR, SUFFIX_FLAIR,
    EXCLUDE_IN_ANAT, EXCLUDE_IN_ANAT_T1,
    FILTERS,
)
from tabular.ppmi_utils import (
    COL_DESCRIPTION_IMAGING,
    COL_MODALITY_IMAGING,
    COL_PROTOCOL_IMAGING,
    MODALITY_ANAT,
    MODALITY_DWI,
    MODALITY_FUNC,
)

# ========== CONSTANTS ==========
FNAME_DESCRIPTIONS = 'ppmi_imaging_descriptions.json' # output file name
FNAME_IGNORED = 'ppmi_imaging_ignored.csv'            # output file name
GLOBAL_CONFIG_DATASET_ROOT = 'DATASET_ROOT'
DPATH_OTHER_RELATIVE = Path('tabular', 'other')  # relative to DATASET_ROOT
FLAG_OVERWRITE = '--overwrite'

# mapping from BIDS datatype/suffix to PPMI "Modality" column
# the PPMI "Modality" column is not 100% accurate so we still have to check description strings
DATATYPE_MODALITY_MAP = {
    DATATYPE_DWI: MODALITY_DWI,
    DATATYPE_FUNC: MODALITY_FUNC,
    DATATYPE_ANAT: MODALITY_ANAT,
    SUFFIX_T1: MODALITY_ANAT,         # anat
    SUFFIX_T2: MODALITY_ANAT,         # anat
    SUFFIX_T2_STAR: MODALITY_ANAT,    # anat
    SUFFIX_FLAIR: MODALITY_ANAT,      # anat
}


def run(global_config_file, overwrite=False, indent=4):

    # parse global config
    with open(global_config_file) as file:
        global_config = json.load(file)
    dpath_dataset = Path(global_config[GLOBAL_CONFIG_DATASET_ROOT])

    # generate filepaths
    dpath_other = dpath_dataset / DPATH_OTHER_RELATIVE
    dpath_out = Path(__file__).parent
    fpath_imaging = dpath_other / global_config['TABULAR']['OTHER']['IMAGING_INFO']['FILENAME']
    fpath_out_descriptions = dpath_out / FNAME_DESCRIPTIONS
    fpath_out_ignored = dpath_out / FNAME_IGNORED

    # load df
    df_imaging = pd.read_csv(fpath_imaging)
    descriptions = {}

    # dwi
    print(f'========== {DATATYPE_DWI} =========='.upper())
    descriptions[DATATYPE_DWI] = filter_descriptions(
        df=df_imaging,
        datatype=DATATYPE_DWI,
        **FILTERS[DATATYPE_DWI],
    )

    # func
    print(f'\n========== {DATATYPE_FUNC} =========='.upper())
    descriptions[DATATYPE_FUNC] = filter_descriptions(
        df=df_imaging,
        datatype=DATATYPE_FUNC,
        **FILTERS[DATATYPE_FUNC],
    )

    # anat (dictionary with image subtypes)
    descriptions[DATATYPE_ANAT] = {}

    # t1
    print(f'\n========== {DATATYPE_ANAT} ({SUFFIX_T1}) =========='.upper())
    descriptions[DATATYPE_ANAT][SUFFIX_T1] = filter_descriptions(
        df=df_imaging,
        datatype=SUFFIX_T1,
        exclude_in=EXCLUDE_IN_ANAT_T1,
        **FILTERS[DATATYPE_ANAT],
        **FILTERS[SUFFIX_T1],
    )

    # t2
    print(f'\n========== {DATATYPE_ANAT} ({SUFFIX_T2}) =========='.upper())
    descriptions[DATATYPE_ANAT][SUFFIX_T2] = filter_descriptions(
        df=df_imaging,
        datatype=SUFFIX_T2,
        exclude_in=EXCLUDE_IN_ANAT + descriptions[DATATYPE_ANAT][SUFFIX_T1],
        **FILTERS[DATATYPE_ANAT],
        **FILTERS[SUFFIX_T2],
    )

    # t2 star
    print(f'\n========== {DATATYPE_ANAT} ({SUFFIX_T2_STAR}) =========='.upper())
    descriptions[DATATYPE_ANAT][SUFFIX_T2_STAR] = filter_descriptions(
        df=df_imaging,
        datatype=SUFFIX_T2_STAR,
        exclude_in=EXCLUDE_IN_ANAT + descriptions[DATATYPE_ANAT][SUFFIX_T1] + descriptions[DATATYPE_ANAT][SUFFIX_T2],
        **FILTERS[DATATYPE_ANAT],
        **FILTERS[SUFFIX_T2_STAR],
    )

    # flair
    print(f'\n========== {DATATYPE_ANAT} ({SUFFIX_FLAIR}) =========='.upper())
    descriptions[DATATYPE_ANAT][SUFFIX_FLAIR] = filter_descriptions(
        df=df_imaging,
        datatype=SUFFIX_FLAIR,
        exclude_in=EXCLUDE_IN_ANAT + descriptions[DATATYPE_ANAT][SUFFIX_T1] + descriptions[DATATYPE_ANAT][SUFFIX_T2],
        **FILTERS[DATATYPE_ANAT],
        **FILTERS[SUFFIX_FLAIR],
    )

    # # anat: T1 + T2 + T2* + FLAIR
    # descriptions[DATATYPE_ANAT] = sorted(list(set(
    #     descriptions[SUFFIX_T1] + descriptions[SUFFIX_T2] + descriptions[SUFFIX_T2_STAR] + descriptions[SUFFIX_FLAIR]
    # )))

    print(f'\nFINAL DESCRIPTIONS:')
    # descriptions_all = []
    # for datatype, datatype_descriptions in descriptions.items():
    #     descriptions_all.extend(datatype_descriptions)
    #     print(f'{datatype}:\t{len(datatype_descriptions)}')
    descriptions_all = get_all_descriptions(descriptions, verbose=True)

    # check if output file already exists
    for fpath in [fpath_out_descriptions, fpath_out_ignored]:
        if fpath.exists() and not overwrite:
            raise FileExistsError(f'File exists: {fpath}. Use {FLAG_OVERWRITE} to overwrite')

    # save
    with fpath_out_descriptions.open('w') as file_out:
        json.dump(descriptions, file_out, indent=indent)
    print(f'JSON file with datatype-descriptions mapping written to: {fpath_out_descriptions}')

    # save another file with all images that didn't make it in any datatype
    df_ignored: pd.DataFrame = df_imaging.loc[
        ~df_imaging[COL_DESCRIPTION_IMAGING].isin(descriptions_all),
        COL_DESCRIPTION_IMAGING,
    ].drop_duplicates().sort_values()
    df_ignored.to_csv(fpath_out_ignored, index=False)
    print(f'Ignored descriptions written to: {fpath_out_ignored}')


def filter_descriptions(
        df: pd.DataFrame, 
        datatype, 
        common_substrings, 
        reject_substrings=None, 
        reject_substrings_exceptions=None, 
        exclude_in=None, 
        exclude_out=None, 
        protocol_include=None, 
        protocol_exclude=None,
    ):
    """Return a list of description strings corresponding to the datatype.

    Parameters
    ----------
    df : pd.DataFrame
        Input imaging data information
    datatype : str
        String for mapping to modality value
    common_substrings : list[str]
        Substrings commonly found in descriptions strings for this datatype
    reject_substrings : list[str] or None, optional
        Substrings in descriptions that should be rejected for this datatype, by default None
    reject_substrings_exceptions : list[str] or None, optional
        Exceptions for reject_substrings (e.g., 'T1 REPEAT2' has 'T2' but is a T1), by default None
    exclude_in : list[str] or None, optional
        Descriptions to exclude in within-modality search, by default None
    exclude_out : list[str] or None, optional
        Descriptions to exclude in out-of-modality search, by default None
    protocol_include : list[str] or None, optional
        Substrings required in imaging protocol column (e.g., Acquisition Type), by default None
    protocol_exclude : list[str] or None, optional
        Substrings to reject in imaging protocol column (e.g., Acquisition Type), by default None

    Returns
    -------
    list[str]
        The descriptions after all filtering operations
    """
    modality = DATATYPE_MODALITY_MAP[datatype]

    # filter based on imaging protocol column (e.g., Weighting, Acquisition Type)
    # rows that are excluded are completely rejected (not considered 'out-of-modality')
    protocol_filters_str = ''
    if protocol_include is not None:
        df = df.loc[
            df[COL_PROTOCOL_IMAGING].str.lower().str.contains('|'.join(protocol_include).lower(), na=False)
        ]
        protocol_filters_str = f'{protocol_filters_str}\n\t- WITH: {", ".join(protocol_include)}'
    if protocol_exclude is not None:
        df = df.loc[
            ~df[COL_PROTOCOL_IMAGING].str.lower().str.contains('|'.join(protocol_exclude).lower(), na=False)
        ]
        protocol_filters_str = f'{protocol_filters_str}\n\t- WITHOUT: {", ".join(protocol_exclude)}'
    
    # initial set of descriptions
    df_modality = df.loc[df[COL_MODALITY_IMAGING] == modality]
    descriptions = df_modality[COL_DESCRIPTION_IMAGING].value_counts()
    print(f'Found {len(descriptions)} unique description strings for modality {modality}{protocol_filters_str}')

    # remove bad descriptions
    if exclude_in is not None and len(exclude_in) > 0:
        descriptions = descriptions.loc[~descriptions.index.isin(exclude_in)]
        if len(exclude_in) > 10:
            exclude_in_str = f'{len(exclude_in)} descriptions'
        else:
            exclude_in_str = f'{exclude_in}'
        print(f'\nGot {len(descriptions)} unique descriptions after removing {exclude_in_str}')

    # filter based on description strings (substring matching)
    if reject_substrings is not None and len(reject_substrings) > 0:

        if reject_substrings_exceptions is not None:
            descriptions_keep = descriptions.loc[
                descriptions.index.str.lower().str.contains('|'.join(reject_substrings_exceptions).lower())
            ]
            reject_substrings_exceptions_str = f' (except {reject_substrings_exceptions})'
        else:
            descriptions_keep = None
            reject_substrings_exceptions_str = ''

        descriptions = descriptions.loc[
            ~descriptions.index.str.lower().str.contains('|'.join(reject_substrings).lower())
        ]

        descriptions = pd.concat([descriptions, descriptions_keep])
        descriptions = descriptions.loc[~descriptions.index.duplicated()]

        print(f'\nGot {len(descriptions)} unique descriptions after removing those that contained one of {reject_substrings}{reject_substrings_exceptions_str}')

    # find descriptions that don't contain a common substring
    suspicious_descriptions = descriptions.loc[~descriptions.index.str.lower().str.contains('|'.join(common_substrings).lower())]
    print(f'\n{len(suspicious_descriptions)} descriptions out of {len(descriptions)} do not contain any of {common_substrings}')
    print(f'Make sure that they are indeed {datatype.upper()}, otherwise add them to exclude_in list')
    print('-'*30)
    print(suspicious_descriptions)

    # check other modalities
    df_other_modalities = df.loc[~df.index.isin(df_modality.index)]

    # remove known bad descriptions
    exclude_out_str = ''
    if exclude_out is not None and len(exclude_out) > 0:
        df_other_modalities = df_other_modalities.loc[
            ~df_other_modalities[COL_DESCRIPTION_IMAGING].isin(exclude_out)
        ]
        exclude_out_str = f' (after removing {exclude_out})'

    # check if any of the previously found descriptions are in another modality
    common_descriptions_other_modalities = df_other_modalities.loc[
        (df_other_modalities[COL_DESCRIPTION_IMAGING].isin(descriptions.index)),
        COL_DESCRIPTION_IMAGING,
    ].value_counts()
    if len(common_descriptions_other_modalities) > 0:
        print(
            f'\nFound {len(common_descriptions_other_modalities)}'
            ' common descriptions with other modalities'
        )
        print(f'Make sure that they are indeed {datatype.upper()}, otherwise add them to exclude_out list')
        print('-'*30)
        print(common_descriptions_other_modalities)

    # find descriptions in other modalities that have a common substring
    descriptions_new = df_other_modalities.loc[
        (
            (df_other_modalities[COL_DESCRIPTION_IMAGING].str.lower().str.contains('|'.join(common_substrings).lower()))
            & (~df_other_modalities[COL_DESCRIPTION_IMAGING].isin(descriptions.index))
        ),
        COL_DESCRIPTION_IMAGING,
    ].value_counts()
    if len(descriptions_new) > 0:
        print(
            f"\n{'!'*30}"
            f'\nFound {len(descriptions_new)} new description string(s) with one'
            f' of {common_substrings} in another modality{exclude_out_str}'
        )
        print(f'Make sure that they are indeed {datatype.upper()}, otherwise add them to exclude_out list')
        print(descriptions_new)

    # combine
    descriptions = sorted(pd.concat([descriptions, descriptions_new]).index.drop_duplicates().to_list())

    return descriptions


def get_all_descriptions(descriptions_dict, verbose=False):
    
    def _get_all_descriptions(descriptions_dict_or_list, descriptions, print_prefix):
        if isinstance(descriptions_dict_or_list, dict):
            for key, descriptions_subdict_or_list in descriptions_dict_or_list.items():
                if verbose:
                    print(f'{print_prefix}{key}:', end='')
                descriptions = _get_all_descriptions(descriptions_subdict_or_list, descriptions, f'\t{print_prefix}')
        else:
            if verbose:
                print(f' {len(descriptions_dict_or_list)}')
            descriptions.extend(descriptions_dict_or_list)
        return descriptions

    return _get_all_descriptions(descriptions_dict, [], '')


if __name__ == '__main__':
    # argparse
    HELPTEXT = f"""
    Script to generate generate lists of protocol names for various datatypes and sub-datatypes. 
    Also creates a CSV file with all images with a description not matching any datatype. 
    Requires an imaging data availability info file that can be downloaded from 
    the LONI IDA. File should be in [DATASET_ROOT]/{DPATH_OTHER_RELATIVE}.
    """
    parser = argparse.ArgumentParser(description=HELPTEXT)
    parser.add_argument(
        '--global_config', type=str, required=True,
        help='path to global config file for your nipoppy dataset (required)')
    parser.add_argument(
        FLAG_OVERWRITE, action='store_true',
        help=(f'overwrite any existing {FNAME_DESCRIPTIONS} file')
    )
    args = parser.parse_args()

    # parse
    global_config_file = args.global_config
    overwrite = args.overwrite

    run(global_config_file, overwrite=overwrite)

