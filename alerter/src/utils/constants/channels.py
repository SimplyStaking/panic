# Templates
EMAIL_HTML_TEMPLATE = """<style type="text/css">
.email {{font-family: sans-serif}}
.tg  {{border:none; border-spacing:0;border-collapse: collapse;}}
.tg td{{border-style:none;border-width:0px;overflow:hidden; padding:10px 5px;word-break:normal;}}
.tg th{{border-style:none;border-width:0px;overflow:hidden;padding:10px 5px;word-break:normal;text-align:left;background-color:lightgray;}}
@media screen and (max-width: 767px) {{.tg {{width: auto !important;}}.tg col {{width: auto !important;}}.tg-wrap {{overflow-x: auto;-webkit-overflow-scrolling: touch;}} }}</style>
<div class="email">
<h2>PANIC Alert</h2>
<p>An alert was generated with the following details:</p>
<div class="tg-wrap"><table class="tg">
<tbody>
  <tr>
    <th>Alert Code:</th>
    <td>{alert_code}</td>
  </tr>
  <tr>
    <th>Severity:</th>
    <td>{severity}</td>
  </tr>
  <tr>
    <th>Message:</th>
    <td>{message}</td>
  </tr>
  <tr>
    <th>Triggered At:</th>
    <td>{date_time}</td>
  </tr>
  <tr>
    <th>Parent ID:</th>
    <td>{parent_id}</td>
  </tr>
  <tr>
    <th>Origin ID:</th>
    <td>{origin_id}</td>
  </tr>
</tbody>
</table></div>
</div>"""
EMAIL_TEXT_TEMPLATE = """
PANIC Alert!
======================
An alert was generated with the following details:

Alert Code: {alert_code}
Severity: {severity}
Message: {message}
Triggered At: {date_time}
Parent ID: {parent_id}
Origin ID: {origin_id}
"""
