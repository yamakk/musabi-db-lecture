width = 2200
tall = 26000
short = tall / 3
height = tall
margin = 100
duration_ms = 1500
img_w = 200
img_h = 200
data_name = "oscar.tsv?#{new Date().getTime()}"

svg = d3.select('.graph')
  .append('svg')
  .attr("height", height)
  .attr("width", width)
  .style("background", '#EFEFEF')

Array::unique = ->
  output = {}
  output[@[key]] = @[key] for key in [0...@length]
  value for key, value of output

substr = (s, max)->
  if s.length > max then s.substr(0, max) + '...' else s

sc_mon = d3.scale.linear().range([5, 300])
sc_x = d3.scale.linear().domain([0,10]).range([margin*3, width-margin])
sc_year = d3.scale.linear().domain([2012, 1926]).range([margin, height])

swith_poster = (opacity)->
  svg.selectAll('image.poster')
    .transition()
    .duration(duration_ms)
    .style('opacity', opacity)

update = (ds) ->
  #console.log(ds)#parseFloat(item.budget) for item in csv)
  moneys = []
  for movie in ds
    budget = parseFloat(movie.budget)
    bo = parseFloat(movie.bo)
    if not isNaN(budget)
      moneys.push (budget * (100.0/movie.cpi))
    if not isNaN(bo)
      moneys.push (bo * (100.0/movie.cpi))
  sc_mon.domain(d3.extent moneys)

  hide_money =->
    svg.selectAll('text.money-label')
      .transition()
      .duration(duration_ms/8)
      .style('opacity',0)
  show_money =(d)->
    if height == short
      svg.select("#num#{d.num}")
          .transition()
          .duration(duration_ms/4)
          .style('opacity', 0.8)

  # group
  movies = svg.selectAll('g.movie')
    .data(ds).enter()
    .append('g')
    .attr('class', 'movie')

  # poster
  movies.append('image')
    .attr('class', 'poster')
    .attr('x', (d)-> sc_x d.order)
    .attr('y', 55)
    .attr('width', img_w)
    .attr('height', img_h)
    .on('click', (d)->location.href=d.link)
    .attr('alt', (d)->"Budget:$#{d.budget}M Box office:$#{d.bo}M")
    .attr("xlink:href", (d)->"poster/#{d.poster}")
    .attr('transform',(d)->"translate(#{-1*img_w/2}, #{0})")
    .style('opacity', 1.0)

  # budget circle
  movies.append('circle')
    .attr('class', 'budget')
    .attr('r',(d)->
        if parseFloat(d.budget) then sc_mon d.budget*(100/d.cpi) else 0)
    .attr('cx',(d)-> sc_x d.order)
    #.attr('cy',(d)-> height)
    #.attr('transform', (d)->"translate(#{sc_x d.order}, #{sc_year d.year})")
    .style('opacity', 0.5)
    .attr('fill','red')
    .on('click', (d)->location.href=d.link)
    .on('mouseover', (d)-> show_money(d))
    .on('mouseout', hide_money)

  # box office circle
  movies.append('circle')
    .attr('class', 'bo')
    .attr('r',(d)->
        if parseFloat(d.bo) then sc_mon d.bo *(100/d.cpi) else 0 )
    # .attr('transform', (d)->"translate(#{sc_x d.order}, #{0})")
    .attr('cx',(d)-> sc_x d.order)
    #.attr('cy',(d)-> sc_year d.year)
    .attr('fill', '#39c')
    .style('opacity', 0.5)
    .on('click', (d)->location.href=d.link)
    .on('mouseover', (d)-> show_money(d))
    .on('mouseout', hide_money)

  # title label
  movies.append('text')
    .attr('class', 'title-label')
    .attr('transform', (d)->"translate(#{0}, #{40})")
    .attr('x',(d,i)->sc_x d.order)
    #.attr('y',(d)-> 45 + sc_year d.year )
    .text((d)->
      title = if d.gp == 'TRUE' then '* '+d.title else d.title
      substr(title, 30))#+'/'+d.year)
    #.style('text-decoration', (d)-> if d.gp then 'underline' else 'none')
    #.style('cursor','pointer')
    .style('opacity', (d)->
        if d.budget == '' or d.bo == '' then 0.4 else 0.9)
    .style('dominant-baseline','auto')
    .style('text-anchor','middle')


  # money label
  movies.append('text')
    .attr('id', (d)->"num#{d.num}")
    .attr('class', 'money-label')
    .attr('transform', (d)->"translate(#{0}, #{60})")
    .attr('x',(d,i)->sc_x d.order)
    .text((d)->
      budget = budget * (100.0 / d.cpi)
      budget = parseInt(parseFloat(d.budget) * 10) / 10
      budget = if budget then "budget $#{budget}m" else ''
      bo = bo * (100.0 / d.cpi)
      bo = parseInt(parseFloat(d.bo) * 10) / 10.0
      bo = if bo then "box office $#{bo}m" else ''
      sp = if bo && budget then ' ' else ''
      "#{budget}#{sp}#{bo}")
    .style('cursor','pointer')
    .style('dominant-baseline','middle')
    .style('text-anchor','middle')
    .style('opacity', 0)

  # year label
  year_list = (d.year for d in ds).unique()
  years = svg.selectAll('g.year')
    .data(year_list).enter()
    .append('g')
    .attr('class', 'year')

  years.append('text')
    .attr('class', 'year-label')
    .attr('x', 60)# font base line
    .text((d)->d)
    .style('opacity', 0.5)


  # -------------------
  # update scale
  # -------------------
  sc_year.range([margin, height])

  svg.selectAll('g.year')
    .transition().duration(duration_ms)
    .attr('transform',(d)->
        "translate(#{0}, #{sc_year d})")

  svg.selectAll('g.movie')
    .transition().duration(duration_ms)
    .attr('transform',(d)->
        "translate(#{0}, #{sc_year d.year})")
  svg.attr('height', height)

init =->
  d3.tsv data_name, (ds) ->
    #for d in ds
    #  console.log(d.budget)
    update ds
    console.log 'now'
    #swith_poster(1)
    setTimeout( ()->
      console.log '300'
      height = short
      update ds
      swith_poster 0
    , duration_ms*2)

    svg.on 'click', ()->
      if height == tall
        height = short
        update ds
        swith_poster 0
      else
        height = tall
        update ds
        swith_poster 1
init()
