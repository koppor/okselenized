#! bash oh-my-bash.module
# OkSelenized prompt theme for oh-my-bash, based on duru
# (https://github.com/ohmybash/oh-my-bash/wiki/Themes#copied-duru)
# with the full working directory instead of the last two dirs.
#
# Colors are ANSI slot references, so the prompt renders in whatever
# OkSelenized variant (dark/black/light) the terminal has applied.
#
# Install:
#   mkdir -p ~/.oh-my-bash/custom/themes/okselenized
#   cp okselenized.theme.sh ~/.oh-my-bash/custom/themes/okselenized/
#   # in ~/.bashrc: OSH_THEME="okselenized"

SCM_THEME_PROMPT_PREFIX="${_omb_prompt_teal} on ${_omb_prompt_green}"
SCM_THEME_PROMPT_SUFFIX=""
SCM_THEME_PROMPT_DIRTY=" ${_omb_prompt_brown}with changes"
SCM_THEME_PROMPT_CLEAN=""

function venv {
  if [ -n "$VIRTUAL_ENV" ]; then
    _omb_util_print "${_omb_prompt_gray} in ${_omb_prompt_red}${VIRTUAL_ENV##*/} "
  fi
}

function _omb_theme_PROMPT_COMMAND {
  PS1="${_omb_prompt_olive}# ${_omb_prompt_reset_color}\w$(scm_prompt_info)${_omb_prompt_reset_color}$(venv)${_omb_prompt_reset_color} ${_omb_prompt_teal}\n> ${_omb_prompt_reset_color}"
}

_omb_util_add_prompt_command _omb_theme_PROMPT_COMMAND
