import React from 'react'
import Typography from '@material-ui/core/Typography';
import Box from '@material-ui/core/Box';


function Title(props) {
    return (
        <Box pt={3}>
            <Typography 
                style={{ textAlign: 'center'}} 
                variant="h2"  
                align="center" 
                gutterBottom>
                {props.text}
            </Typography>
        </Box>
    )
}

export default Title;