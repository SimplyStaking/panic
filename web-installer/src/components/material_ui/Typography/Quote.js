import React from 'react';
// nodejs library to set properties for components
import PropTypes from 'prop-types';
// core components
import useStyles from 'assets/jss/material-kit-react/components/typographyStyle';

export default function Quote(props) {
  const { text, author } = props;
  const classes = useStyles();
  return (
    <blockquote className={`${classes.defaultFontStyle} ${classes.quote}`}>
      <p className={classes.quoteText}>{text}</p>
      <small className={classes.quoteAuthor}>{author}</small>
    </blockquote>
  );
}

Quote.propTypes = {
  text: PropTypes.node.isRequired,
  author: PropTypes.node.isRequired,
};
