# -*- coding: utf-8 -*-
"""
Created on Tue Nov 21 14:19:08 2023

@author: dsite
"""

import streamlit as st
import model.model as model

class Analytics:
    def __init__(self):
        
        # if not model.allow:
        #     exit(0)
        pass

    def setup_session_states(self):
        if 'cube_atoti' not in st.session_state:
            st.session_state.cube_atoti = self.cube_atoti
        if 'segment_actuel' not in st.session_state:
            st.session_state.segment_actuel = 0
            
    def run(self):
        pass
    
