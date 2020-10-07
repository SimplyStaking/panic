import React from 'react'
import Box from '@material-ui/core/Box';

function MainText( props ) {
    return (
        <Box p={5} className="greyBackground">
            <p style={{textAlign:"justify"}}>
                {props.text}
            </p>
        </Box>
    )
}

export default MainText;