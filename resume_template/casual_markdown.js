/*****************************************************************************
 * casual-markdown - a lightweight regexp-base markdown parser with TOC support
 * 2022/07/31, v0.90, refine frontmatter (simple yaml)  
 * 2023/04/12, v0.92, addCopyButton for code-block
 *
 * Copyright (c) 2022-2023, Casualwriter (MIT Licensed)
 * https://github.com/casualwriter/casual-markdown
*****************************************************************************/
;(function(){ 

  // define md object, and extent function (which is a dummy function)
  var md = { yaml:{}, before: function (str) {return str}, after: function (str) {return str} }

  // function for REGEXP to convert html tag. ie. <TAG> => &lt;TAG*gt;  
  md.formatTag = function (html) { return html.replace(/</g,'&lt;').replace(/\>/g,'&gt;'); }

  // frontmatter for simple YAML (support multi-level, but string value only)
  md.formatYAML = function (front, matter) {
    var level = {}, latest = md.yaml;
    matter.replace( /^\s*#(.*)$/gm, '' ).replace( /^( *)([^:^\n]+):(.*)$/gm, function(m, sp, key,val) { 
        level[sp] = level[sp] || latest
        latest = level[sp][key.trim()] = val.trim() || {}
        for (e in level) if(e>sp) level[e]=null;
      } );
    return ''
  }

  //===== format code-block, highlight remarks/keywords for code/sql
  md.formatCode = function (match, title, block) {
    // convert tag <> to &lt; &gt; tab to 3 space, support marker using ^^^
    block = block.replace(/</g,'&lt;').replace(/\>/g,'&gt;')
    block = block.replace(/\t/g,'   ').replace(/\^\^\^(.+?)\^\^\^/g, '<mark>$1</mark>')
    
    // highlight comment and keyword based on title := none | sql | code
    if (title.toLowerCase(title) == 'sql') {
      block = block.replace(/^\-\-(.*)/gm,'<rem>--$1</rem>').replace(/\s\-\-(.*)/gm,' <rem>--$1</rem>')   
      block = block.replace(/(\s?)(function|procedure|return|if|then|else|end|loop|while|or|and|case|when)(\s)/gim,'$1<b>$2</b>$3')
      block = block.replace(/(\s?)(select|update|delete|insert|create|from|where|group by|having|set)(\s)/gim,'$1<b>$2</b>$3')
    } else if ((title||'none')!=='none') {
      block = block.replace(/^\/\/(.*)/gm,'<rem>//$1</rem>').replace(/\s\/\/(.*)/gm,' <rem>//$1</rem>')   
      block = block.replace(/(\s?)(function|procedure|return|exit|if|then|else|end|loop|while|or|and|case|when)(\s)/gim,'$1<b>$2</b>$3')
      block = block.replace(/(\s?)(var|let|const|=>|for|next|do|while|loop|continue|break|switch|try|catch|finally)(\s)/gim,'$1<b>$2</b>$3')
    }
    
    return '<pre title="' + title + '"><button onclick="md.clipboard(this)">copy</button><code>'  + block + '</code></pre>'
  }

  // copy to clipboard for code-block
  md.clipboard = function (e) {
    navigator.clipboard.writeText( e.parentNode.innerText.replace('copy\n','') )
    e.innerText = 'copied'
  }

  //===== parse markdown string into HTML string (exclude code-block)
  md.parser = function( mdstr ) {
  
    // apply yaml variables
    for (var name in this.yaml) mdstr = mdstr.replace( new RegExp('\{\{\\s*'+name+'\\s*\}\}', 'gm'), this.yaml[name] )
    
    // table syntax
    mdstr = mdstr.replace(/\n(.+?)\n.*?\-\-\s?\|\s?\-\-.*?\n([\s\S]*?)\n\s*?\n/g, function (m,p1,p2) {
        var thead = p1.replace(/^\|(.+)/gm,'$1').replace(/(.+)\|$/gm,'$1').replace(/\|/g,'<th>')
        var tbody = p2.replace(/^\|(.+)/gm,'$1').replace(/(.+)\|$/gm,'$1')
        tbody = tbody.replace(/(.+)/gm,'<tr><td>$1</td></tr>').replace(/\|/g,'<td>')
        return '\n<table>\n<thead>\n<th>' + thead + '\n</thead>\n<tbody>' + tbody + '\n</tbody></table>\n\n' 
    } )   

    // horizontal rule => <hr> 
    mdstr = mdstr.replace(/^-{3,}|^\_{3,}|^\*{3,}$/gm, '<hr>').replace(/\n\n<hr\>/g, '\n<br><hr>')

    // header => <h1>..<h5> 
    mdstr = mdstr.replace(/^##### (.*?)\s*#*$/gm, '<h5>$1</h5>')
              .replace(/^#### (.*?)\s*#*$/gm, '<h4>$1</h4>')
              .replace(/^### (.*?)\s*#*$/gm, '<h3>$1</h3>')
              .replace(/^## (.*?)\s*#*$/gm, '<h2>$1</h2>')
              .replace(/^# (.*?)\s*#*$/gm, '<h1>$1</h1>')
              .replace(/^<h(\d)\>(.*?)\s*{(.*)}\s*<\/h\d\>$/gm, '<h$1 id="$3">$2</h$1>')
        
    // inline code-block: `code-block` => <code>code-block</code>    
    mdstr = mdstr.replace(/``(.*?)``/gm, function(m,p){ return '<code>' + md.formatTag(p).replace(/`/g,'&#96;') + '</code>'} ) 
    mdstr = mdstr.replace(/`(.*?)`/gm, '<code>$1</code>' )
        
    // blockquote, max 2 levels => <blockquote>{text}</blockquote>
    mdstr = mdstr.replace(/^\>\> (.*$)/gm, '<blockquote><blockquote>$1</blockquote></blockquote>')
    mdstr = mdstr.replace(/^\> (.*$)/gm, '<blockquote>$1</blockquote>')
    mdstr = mdstr.replace(/<\/blockquote\>\n<blockquote\>/g, '\n<br>' )
    mdstr = mdstr.replace(/<\/blockquote\>\n<br\><blockquote\>/g, '\n<br>' )
                  
    // image syntax: ![title](url) => <img alt="title" src="url" />          
    mdstr = mdstr.replace(/!\[(.*?)\]\((.*?) "(.*?)"\)/gm, '<img alt="$1" src="$2" $3 />')
    mdstr = mdstr.replace(/!\[(.*?)\]\((.*?)\)/gm, '<img alt="$1" src="$2" width="90%" />')
                  
    // links syntax: [title "title"](url) => <a href="url" title="title">text</a>          
    mdstr = mdstr.replace(/\[(.*?)\]\((.*?) "new"\)/gm, '<a href="$2" target=_new>$1</a>')
    mdstr = mdstr.replace(/\[(.*?)\]\((.*?) "(.*?)"\)/gm, '<a href="$2" title="$3">$1</a>')
    mdstr = mdstr.replace(/([<\s])(https?\:\/\/.*?)([\s\>])/gm, '$1<a href="$2">$2</a>$3')
    mdstr = mdstr.replace(/\[(.*?)\]\(\)/gm, '<a href="$1">$1</a>')
    mdstr = mdstr.replace(/\[(.*?)\]\((.*?)\)/gm, '<a href="$2">$1</a>')
                  
    // unordered/ordered list, max 2 levels  => <ul><li>..</li></ul>, <ol><li>..</li></ol>
    mdstr = mdstr.replace(/^[\*+-][ .](.*)/gm, '<ul><li>$1</li></ul>' )
    mdstr = mdstr.replace(/^\d\d?[ .](.*)/gm, '<ol><li>$1</li></ol>' )
    mdstr = mdstr.replace(/^\s{2,6}[\*+-][ .](.*)/gm, '<ul><ul><li>$1</li></ul></ul>' )
    mdstr = mdstr.replace(/^\s{2,6}\d[ .](.*)/gm, '<ul><ol><li>$1</li></ol></ul>' )
    mdstr = mdstr.replace(/<\/[ou]l\>\n\n?<[ou]l\>/g, '\n' )
    mdstr = mdstr.replace(/<\/[ou]l\>\n<[ou]l\>/g, '\n' )
                  
    // text decoration: bold, italic, underline, strikethrough, highlight                
    mdstr = mdstr.replace(/\*\*\*(\w.*?[^\\])\*\*\*/gm, '<b><em>$1</em></b>')
    mdstr = mdstr.replace(/\*\*(\w.*?[^\\])\*\*/gm, '<b>$1</b>')
    mdstr = mdstr.replace(/\*(\w.*?[^\\])\*/gm, '<em>$1</em>')
    mdstr = mdstr.replace(/___(\w.*?[^\\])___/gm, '<b><em>$1</em></b>')
    mdstr = mdstr.replace(/__(\w.*?[^\\])__/gm, '<u>$1</u>')
    // mdstr = mdstr.replace(/_(\w.*?[^\\])_/gm, '<u>$1</u>')  // NOT support!! 
    mdstr = mdstr.replace(/\^\^\^(.+?)\^\^\^/gm, '<mark>$1</mark>')
    mdstr = mdstr.replace(/\^\^(\w.*?)\^\^/gm, '<ins>$1</ins>')
    mdstr = mdstr.replace(/~~(\w.*?)~~/gm, '<del>$1</del>')
                  
    // line break and paragraph => <br/> <p>                
    mdstr = mdstr.replace(/  \n/g, '\n<br/>').replace(/\n\s*\n/g, '\n<p>\n')
        
    // indent as code-block          
    mdstr = mdstr.replace(/^ {4,10}(.*)/gm, function(m,p) { return '<pre><code>' + md.formatTag(p) + '</code></pre>'} )
    mdstr = mdstr.replace(/^\t(.*)/gm, function(m,p) { return '<pre><code>' + md.formatTag(p) + '</code></pre>'} )
    mdstr = mdstr.replace(/<\/code\><\/pre\>\n<pre\><code\>/g, '\n' )

    // Escaping Characters                
    return mdstr.replace(/\\([`_~\*\+\-\.\^\\\<\>\(\)\[\]])/gm, '$1' )
  }

  //===== parse markdown string into HTML content (cater code-block)
  md.html = function (mdText) { 
    // replace \r\n to \n, and handle front matter for simple YAML
    mdText = mdText.replace(/\r\n/g, '\n').replace( /^---+\s*\n([\s\S]*?)\n---+\s*\n/, md.formatYAML )
    // handle code-block.
    mdText = mdText.replace(/\n~~~/g,'\n```').replace(/\n``` *(.*?)\n([\s\S]*?)\n``` *\n/g, md.formatCode)
    
    // split by "<code>", skip for code-block and process normal text
    var pos1=0, pos2=0, mdHTML = ''
    while ( (pos1 = mdText.indexOf('<code>')) >= 0 ) {
      pos2 = mdText.indexOf('</code>', pos1 )
      mdHTML += md.after( md.parser( md.before( mdText.substr(0,pos1) ) ) )
      mdHTML += mdText.substr(pos1, (pos2>0? pos2-pos1+7 : mdtext.length) )
      mdText = mdText.substr( pos2 + 7 )
    }

    return '<div class="markdown">' + mdHTML + md.after( md.parser( md.before(mdText) ) ) + '</div>'
  }
  
  //===== TOC support
  md.toc = function (srcDiv, tocDiv, options ) {

    // select elements, set title
    var tocSelector = (options&&options.css) || 'h1,h2,h3,h4'
    var tocTitle = (options&&options.title) || 'Table of Contents'
    var toc = document.getElementById(srcDiv).querySelectorAll( tocSelector )
    var html = '<div class="toc"><ul>' + (tocTitle=='none'? '' : '<h3>' + tocTitle + '</h3>');
    
    // loop for each element,add <li> element with class in TAG name.
    for (var i=0; i<toc.length; i++ ) {
      if (toc[i].id.substr(0,6)=='no-toc') continue;
      if (!toc[i].id) toc[i].id = "toc-item-" + i;
      html += '<li class="' + toc[i].nodeName + '" title="#' + toc[i].id + '" onclick="location=this.title">' 
      html += toc[i].textContent + '</a></li>';
    }
    
    document.getElementById(tocDiv).innerHTML = html + "</ul>";

    //===== scrollspy support (ps: add to document.body if element(scrollspy) not found)
    if ( options && options.scrollspy ) {
      
      (document.getElementById(options.scrollspy)||document).onscroll = function () {
      
          // get TOC elements, and viewport position   
          var list = document.getElementById(tocDiv).querySelectorAll('li')
          var divScroll = document.getElementById(options.scrollspy) || document.documentElement
          var divHeight = divScroll.clientHeight || divScroll.offsetHeight 
          
          // loop for each TOC element, add/remove scrollspy class
          for (var i=0; i<list.length; i++) {
            var div = document.getElementById( list[i].title.substr(1) )
            var pos = (div? div.offsetTop - divScroll.scrollTop + 10: 0 )  
            if ( pos>0 && pos<divHeight ) {
              list[i].className = list[i].className.replace('active','') + ' active' // classList.add( 'active' );
            } else {
              list[i].className = list[i].className.replace('active','') // classList.remove( 'active' );
            }
          }
        }
      
    }
    //===== end of scrollspy
  }  
  
  if (typeof exports==='object') { 
    module.exports=md;
  } else if (typeof define==='function') { 
     define(function(){return md;});
  } else {
     this.md=md;
  }
}).call( function(){ return this||(typeof window!=='undefined'?window:global)}() );