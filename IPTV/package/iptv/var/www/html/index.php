<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="bootstrap.min.css">
<title>TV Streaming</title>
</head>
<?php
if ( !empty($_GET) ) {
	if ( isset($_GET["start"]) == TRUE ) system( 'sudo systemctl start iptv' );
	elseif ( isset($_GET["restart"]) == TRUE ) system( 'sudo systemctl restart iptv' );
	elseif ( isset($_GET["stop"]) == TRUE ) system( 'sudo systemctl stop iptv' );
	elseif ( isset($_GET["shutdown"]) == TRUE ) system( 'sudo systemctl poweroff' );
	header('Location: index.php');
}
?>
<body>
<div class="container">
<h1>TV Streaming</h1>
<a role="button" href="index.php?start" class="btn btn-success">Start</a>
<a role="button" href="index.php?restart" class="btn btn-warning">Restart</a>
<a role="button" href="index.php?stop" class="btn btn-danger">Stop</a>
<a role="button" href="index.php?shutdown" class="btn btn-secondary">Shutdown</a>
<br />
<?php
echo '<pre>';
system( 'systemctl status iptv', $error );
echo '</pre>';
if ( $error == 0 ) echo '<div class="alert alert-success"><strong>Success!</strong> IPTV service is started</div>';
else echo '<div class="alert alert-danger"><strong>Failed!</strong> IPTV service is not started</div>';
echo '<pre>';
system( 'sudo journalctl -xb | grep \'dvblast\[\'' );
echo '</pre>';
?>
</div>
</body>
</html>
