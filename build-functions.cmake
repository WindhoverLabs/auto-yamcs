set(AUTO_YAMCS_INSTALL_DIR ${CMAKE_CURRENT_LIST_DIR})

  

function(commander_initialize_workspace)
#    set(TARGET_NAME ${ARGV0})
#    cmake_parse_arguments(PARSED_ARGS "" "CONFIG_FILE;OUTPUT_DB_FILE;WORKSPACE_TEMPLATE;WORKSPACE_OUTPUT_PATH;OUTPUT_XTCE_FILE;XTCE_CONFIG_FILE" "" ${ARGN}) 
#    
#    add_custom_target(${TARGET_NAME}
#        COMMAND mkdir ${PARSED_ARGS_WORKSPACE_OUTPUT_PATH} || true
#        COMMAND cp -n -R ${PARSED_ARGS_WORKSPACE_TEMPLATE}/* ${PARSED_ARGS_WORKSPACE_OUTPUT_PATH}/ || true
#        COMMAND yaml-merge  ${PARSED_ARGS_XTCE_CONFIG_FILE} ${PARSED_ARGS_CONFIG_FILE} --overwrite ${PARSED_ARGS_CONFIG_FILE}
#        COMMAND cp -R ${PARSED_ARGS_CONFIG_FILE} ${PARSED_ARGS_WORKSPACE_OUTPUT_PATH}/etc/registry.yaml
#        COMMAND ${AUTO_YAMCS_INSTALL_DIR}/src/generate_xtce.sh ${PARSED_ARGS_CONFIG_FILE} ${PARSED_ARGS_WORKSPACE_OUTPUT_PATH}/${PARSED_ARGS_OUTPUT_DB_FILE} ${PARSED_ARGS_WORKSPACE_OUTPUT_PATH}/${PARSED_ARGS_OUTPUT_XTCE_FILE}
#    )
#
#    # Save the yaml file path and file name so we can add to it later when we add modules
#    set_target_properties(${TARGET_NAME} PROPERTIES YAML_FILE ${PARSED_ARGS_CONFIG_FILE})
        
endfunction()



function(commander_add_module)    
    # Define the function arguments.
    set(MODULE_NAME ${ARGV0})
    cmake_parse_arguments(PARSED_ARGS "" "TARGET_NAME;YAML_PATH;OUTPUT_FILE" "" ${ARGN})

    #get_target_property(YAML_FILE ${PARSED_ARGS_TARGET_WORKSPACE} YAML_FILE)
    
    # Add the executable to the combined design+configuration yaml file
    #execute_process(
    #    #COMMAND echo yaml-set --change=${PARSED_ARGS_YAML_PATH}.elf_files[0] --value=$<TARGET_FILE:${PARSED_ARGS_TARGET_NAME}> ${PARSED_ARGS_OUTPUT_FILE}
    #    COMMAND yaml-set --change=${PARSED_ARGS_YAML_PATH}.elf_files[0] --value=$<TARGET_FILE:${PARSED_ARGS_TARGET_NAME}> ${PARSED_ARGS_OUTPUT_FILE}
    #)
    
    add_custom_target(${MODULE_NAME}_yaml
        COMMAND pwd
        COMMAND yaml-set --change=${PARSED_ARGS_YAML_PATH}.elf_files[0] --value=$<TARGET_FILE:${PARSED_ARGS_TARGET_NAME}> ${PARSED_ARGS_OUTPUT_FILE}
    )

    #message("*****************")
    #message(${PARSED_ARGS_TARGET_NAME})
    #message(${MODULE_NAME}_yaml)
    #add_dependencies(${MODULE_NAME}_yaml ground-tools)
    add_dependencies(ground-tools ${MODULE_NAME}_yaml)
endfunction()


function(commander_add_prebuilt_module)    
    # Define the function arguments.
    set(MODULE_NAME ${ARGV0})
    cmake_parse_arguments(PARSED_ARGS "" "FILE_NAME;YAML_PATH;OUTPUT_FILE;ELF_FILE" "" ${ARGN})

    #get_target_property(YAML_FILE ${PARSED_ARGS_TARGET_WORKSPACE} YAML_FILE)
    
    # Add the executable to the combined design+configuration yaml file
    #execute_process(
    #    #COMMAND echo yaml-set --change=${PARSED_ARGS_YAML_PATH}.elf_files[0] --value=$<TARGET_FILE:${PARSED_ARGS_TARGET_NAME}> ${PARSED_ARGS_OUTPUT_FILE}
    #    COMMAND yaml-set --change=${PARSED_ARGS_YAML_PATH}.elf_files[0] --value=$<TARGET_FILE:${PARSED_ARGS_TARGET_NAME}> ${PARSED_ARGS_OUTPUT_FILE}
    #)
    
    add_custom_target(${MODULE_NAME}_yaml
        COMMAND pwd
        COMMAND yaml-set --change=${PARSED_ARGS_YAML_PATH}.elf_files[0] --value=${PARSED_ARGS_ELF_FILE} ${PARSED_ARGS_OUTPUT_FILE}
    )

    #message("*****************")
    #message(${PARSED_ARGS_TARGET_NAME})
    #message(${MODULE_NAME}_yaml)
    #add_dependencies(${MODULE_NAME}_yaml ground-tools)
    add_dependencies(ground-tools ${MODULE_NAME}_yaml)
endfunction()
