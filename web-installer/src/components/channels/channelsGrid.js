import React from 'react'
import { makeStyles } from '@material-ui/core/styles';
import Paper from '@material-ui/core/Paper';
import { Grid, Box, Button } from '@material-ui/core'

import PagerDutyIcon from '../../assets/icons/pagerduty.svg';
import EmailIcon from '../../assets/icons/email.svg';
import TelegramIcon from '../../assets/icons/telegram.svg';
import TwilioIcon from '../../assets/icons/twilio.svg';
import OpsGenieIcon from '../../assets/icons/opsGenie.svg';

const useStyles = makeStyles((theme) => ({
    root: {
        flexGrow: 1,
    },
    paper: {
        padding: theme.spacing(2),
        textAlign: 'center',
        color: theme.palette.text.primary,
    },
    icon: {
        width:"5%",
        paddingRight: '1rem',
    }
}));

function ChannelsGrid() {

    const classes = useStyles();

    return (
        <Box p={2} className={classes.root}>
            <Box 
                p={3} 
                border={1} 
                borderRadius="borderRadius"
                borderColor="grey.300">

                <Grid container spacing={3}>
                    <Grid item xs={6}>
                        <Paper>
                            <Button className={classes.paper} fullWidth fullHeight> 
                                <img 
                                    src={TelegramIcon} 
                                    className={classes.icon}
                                    alt="TelegramIcon"/>
                                Telegram
                            </Button>
                        </Paper>
                    </Grid>
                    <Grid item xs={6}>
                        <Paper>
                            <Button className={classes.paper} fullWidth fullHeight> 
                                <img 
                                    src={TwilioIcon}
                                    className={classes.icon}
                                    alt="TwilioIcon"/>
                                Twilio
                            </Button>
                        </Paper>
                    </Grid>
                    <Grid item xs={6}>
                        <Paper>
                            <Button className={classes.paper} fullWidth fullHeight> 
                            <img 
                                src={EmailIcon}
                                className={classes.icon}
                                alt="EmailIcon"/>
                                Email
                            </Button>
                        </Paper>
                    </Grid>
                    <Grid item xs={6}>
                        <Paper>
                            <Button className={classes.paper} fullWidth fullHeight>
                            <img 
                                src={PagerDutyIcon}
                                className={classes.icon}
                                alt="PagerDutyIcon"/>
                                PagerDuty
                            </Button>
                        </Paper>
                    </Grid>
                    <Grid item xs={6}>
                        <Paper>
                            <Button className={classes.paper} fullWidth fullHeight> 
                                <img 
                                    src={OpsGenieIcon}  
                                    className={classes.icon}
                                    alt="OpsGenieIcon"/>
                                OpsGenie
                            </Button>
                        </Paper>
                    </Grid>
                </Grid>
            </Box>
        </Box>
    );
}


export default ChannelsGrid;