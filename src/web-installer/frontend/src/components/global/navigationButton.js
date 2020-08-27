import React from 'react'
import { Button, Box } from '@material-ui/core';

const NavigationButton = (props) => {
    
    function triggerNextPage(e) {
        e.preventDefault();
        props.nextPage(props.navigation)
    }

    return (
        <Box p={5} style={{float:"right"}}>
            <Button 
                onClick={triggerNextPage}
                size="large" 
                variant="outlined" 
                color="primary">
                {props.buttonText}
            </Button>
        </Box>
    )
}

export default NavigationButton;