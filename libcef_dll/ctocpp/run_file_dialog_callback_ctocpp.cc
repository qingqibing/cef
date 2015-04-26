// Copyright (c) 2015 The Chromium Embedded Framework Authors. All rights
// reserved. Use of this source code is governed by a BSD-style license that
// can be found in the LICENSE file.
//
// ---------------------------------------------------------------------------
//
// This file was generated by the CEF translator tool. If making changes by
// hand only do so within the body of existing method and function
// implementations. See the translator.README.txt file in the tools directory
// for more information.
//

#include "libcef_dll/ctocpp/run_file_dialog_callback_ctocpp.h"
#include "libcef_dll/transfer_util.h"


// VIRTUAL METHODS - Body may be edited by hand.

void CefRunFileDialogCallbackCToCpp::OnFileDialogDismissed(
    int selected_accept_filter, const std::vector<CefString>& file_paths) {
  cef_run_file_dialog_callback_t* _struct = GetStruct();
  if (CEF_MEMBER_MISSING(_struct, on_file_dialog_dismissed))
    return;

  // AUTO-GENERATED CONTENT - DELETE THIS COMMENT BEFORE MODIFYING

  // Verify param: selected_accept_filter; type: simple_byval
  DCHECK_GE(selected_accept_filter, 0);
  if (selected_accept_filter < 0)
    return;
  // Unverified params: file_paths

  // Translate param: file_paths; type: string_vec_byref_const
  cef_string_list_t file_pathsList = cef_string_list_alloc();
  DCHECK(file_pathsList);
  if (file_pathsList)
    transfer_string_list_contents(file_paths, file_pathsList);

  // Execute
  _struct->on_file_dialog_dismissed(_struct,
      selected_accept_filter,
      file_pathsList);

  // Restore param:file_paths; type: string_vec_byref_const
  if (file_pathsList)
    cef_string_list_free(file_pathsList);
}


// CONSTRUCTOR - Do not edit by hand.

CefRunFileDialogCallbackCToCpp::CefRunFileDialogCallbackCToCpp() {
}

template<> cef_run_file_dialog_callback_t* CefCToCpp<CefRunFileDialogCallbackCToCpp,
    CefRunFileDialogCallback, cef_run_file_dialog_callback_t>::UnwrapDerived(
    CefWrapperType type, CefRunFileDialogCallback* c) {
  NOTREACHED() << "Unexpected class type: " << type;
  return NULL;
}

#ifndef NDEBUG
template<> base::AtomicRefCount CefCToCpp<CefRunFileDialogCallbackCToCpp,
    CefRunFileDialogCallback, cef_run_file_dialog_callback_t>::DebugObjCt = 0;
#endif

template<> CefWrapperType CefCToCpp<CefRunFileDialogCallbackCToCpp,
    CefRunFileDialogCallback, cef_run_file_dialog_callback_t>::kWrapperType =
    WT_RUN_FILE_DIALOG_CALLBACK;
