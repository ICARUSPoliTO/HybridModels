# ui/validators.py

from config import COLORS


class InputValidator:
    @staticmethod
    def validate_float(value, min_value=None, max_value=None, exclusive=False):
        if not value:
            return None
        
        try:
            float_val = float(value)
            
            if min_value is not None:
                if exclusive and float_val <= min_value:
                    return False
                elif not exclusive and float_val < min_value:
                    return False
            
            if max_value is not None:
                if exclusive and float_val >= max_value:
                    return False
                elif not exclusive and float_val > max_value:
                    return False
            
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_int(value, min_value=None, max_value=None, exclusive=False):
        if not value:
            return None
        
        try:
            int_val = int(value)
            float_val = float(int_val)
            
            if min_value is not None:
                if exclusive and float_val <= min_value:
                    return False
                elif not exclusive and float_val < min_value:
                    return False
            
            if max_value is not None:
                if exclusive and float_val >= max_value:
                    return False
                elif not exclusive and float_val > max_value:
                    return False
            
            return True
        except ValueError:
            return False
    
    @staticmethod
    def validate_epsilon(value):
        if not value:
            return None
        
        if value.lower() == "adapt":
            return True
        
        try:
            return float(value) > 1
        except ValueError:
            return False
    
    @staticmethod
    def update_entry_appearance(entry, is_valid):
        if is_valid:
            entry.configure(highlightbackground=COLORS['validation_ok'], 
                          highlightcolor=COLORS['validation_ok'])
        elif is_valid is False:
            entry.configure(highlightbackground=COLORS['validation_error'], 
                          highlightcolor=COLORS['validation_error'])
        else:
            entry.configure(highlightbackground=COLORS['bg_light'], 
                          highlightcolor=COLORS['bg_light'])


def validate_all_inputs(app):
    """
    Validate all inputs in the application
    This function can be called by pages to trigger validation
    """
    # You can implement global validation logic here if needed
    # For now, it's a placeholder that doesn't break the application
    
    # Example implementation (uncomment and modify as needed):
    # all_valid = True
    # 
    # # Validate configuration page inputs
    # if hasattr(app, 'config_page'):
    #     # Add validation checks here
    #     pass
    # 
    # # Validate optimization page inputs
    # if hasattr(app, 'optimization_page'):
    #     # Add validation checks here
    #     pass
    # 
    # return all_valid
    
    pass  # Placeholder for now